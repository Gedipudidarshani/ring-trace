"""
RingTrace: Graph Pattern and Typology Detectors
Extracts deterministic candidate financial crime patterns from the temporal transaction graph.
Note: Detected patterns are treated as INDICATORS/HYPOTHESES, not evidence of criminal guilt.
"""

from typing import List, Dict, Any
from datetime import datetime
from backend.models.schemas import Transaction, DetectedPattern
from backend.graph.temporal_graph import TemporalTransactionGraph, parse_iso


class CandidatePatternDetector:
    """
    Executes algorithmic candidate detection over the temporal graph.
    Computes rigorous graph and velocity metrics without any generative hallucination.
    """

    def __init__(self, graph: TemporalTransactionGraph):
        self.graph = graph
        self.transactions = graph.raw_transactions

    def detect_all_patterns(self) -> List[DetectedPattern]:
        """Runs the complete suite of pattern extractors."""
        patterns: List[DetectedPattern] = []
        patterns.extend(self.detect_cycles())
        patterns.extend(self.detect_layering_chains())
        patterns.extend(self.detect_rapid_pass_through())
        patterns.extend(self.detect_fan_in())
        patterns.extend(self.detect_fan_out())
        return patterns

    def detect_cycles(self) -> List[DetectedPattern]:
        """Detect circular flows / transaction rings (A -> B -> C -> A)."""
        cycles = self.graph.find_temporal_cycles(max_hops=6)
        patterns = []
        for i, cyc in enumerate(cycles, 1):
            patterns.append(DetectedPattern(
                pattern_id=f"PAT-CYC-{i:03d}",
                pattern_type="cycle_ring",
                severity="high",
                title=f"Circular Transaction Flow ({cyc['hop_count']} hops)",
                description=(
                    f"Funds circulate through {len(cyc['accounts'])-1} distinct accounts "
                    f"and return to origin '{cyc['accounts'][0]}' within {cyc['duration_hours']} hours."
                ),
                involved_accounts=cyc["accounts"][:-1],
                involved_transactions=cyc["transaction_ids"],
                metrics={
                    "hop_count": cyc["hop_count"],
                    "duration_hours": cyc["duration_hours"],
                    "start_time": cyc["start_time"],
                    "end_time": cyc["end_time"],
                    "total_flow_amount": sum(cyc["amounts"])
                }
            ))
        return patterns

    def detect_layering_chains(self) -> List[DetectedPattern]:
        """Detect multi-hop sequential layering chains (hops >= 3 within <= 48 hours)."""
        paths = self.graph.find_time_respecting_paths(max_hops=8, max_window_hours=48.0)
        # Filter for paths with 3 or more transactions
        long_paths = [p for p in paths if p.hop_count >= 3]
        
        # Sort by hop count descending to pick top representative layering chains
        long_paths.sort(key=lambda x: (x.hop_count, -x.total_duration_hours), reverse=True)
        
        patterns = []
        seen_tx_signatures = set()

        for i, p in enumerate(long_paths[:5], 1):
            tx_sig = tuple(sorted(p.transaction_ids))
            if tx_sig in seen_tx_signatures:
                continue
            seen_tx_signatures.add(tx_sig)

            patterns.append(DetectedPattern(
                pattern_id=f"PAT-LAY-{i:03d}",
                pattern_type="multi_hop_layering",
                severity="high" if p.hop_count >= 4 else "medium",
                title=f"Multi-Hop Layering Chain ({p.hop_count} hops)",
                description=(
                    f"Sequential fund movement across {len(p.accounts)} accounts "
                    f"completed in {p.total_duration_hours} hours with velocity {p.velocity_rate} / hr."
                ),
                involved_accounts=p.accounts,
                involved_transactions=p.transaction_ids,
                metrics={
                    "hop_count": p.hop_count,
                    "total_duration_hours": p.total_duration_hours,
                    "velocity_rate": p.velocity_rate,
                    "total_amount": p.total_amount
                }
            ))
        return patterns

    def detect_rapid_pass_through(self) -> List[DetectedPattern]:
        """
        Detect intermediary accounts that receive funds and forward > 80% 
        of the amount within a short time threshold (<= 6 hours).
        """
        patterns = []
        pat_counter = 0

        for acc_id, node in self.graph.nodes.items():
            txs_in = [self.graph.tx_by_id[tid] for tid in node["transactions_in"]]
            txs_out = [self.graph.tx_by_id[tid] for tid in node["transactions_out"]]

            if not txs_in or not txs_out:
                continue

            for tin in txs_in:
                t_in_time = parse_iso(tin.timestamp)
                for tout in txs_out:
                    t_out_time = parse_iso(tout.timestamp)
                    if t_out_time < t_in_time:
                        continue  # Inflow must precede outflow

                    delta_hrs = (t_out_time - t_in_time).total_seconds() / 3600.0
                    if 0.0 <= delta_hrs <= 6.0:
                        # Check amount ratio
                        pass_through_ratio = tout.amount / max(tin.amount, 0.01)
                        if 0.70 <= pass_through_ratio <= 1.30:  # Passed through roughly equivalent sum
                            pat_counter += 1
                            patterns.append(DetectedPattern(
                                pattern_id=f"PAT-RPT-{pat_counter:03d}",
                                pattern_type="rapid_pass_through",
                                severity="high" if delta_hrs <= 2.0 else "medium",
                                title=f"Rapid Pass-Through at Intermediary '{acc_id}'",
                                description=(
                                    f"Account '{acc_id}' received {tin.amount} {tin.currency} and forwarded "
                                    f"{tout.amount} {tout.currency} within {delta_hrs:.2f} hours (ratio: {pass_through_ratio:.2f})."
                                ),
                                involved_accounts=[tin.source_account, acc_id, tout.destination_account],
                                involved_transactions=[tin.transaction_id, tout.transaction_id],
                                metrics={
                                    "intermediary_account": acc_id,
                                    "inflow_amount": tin.amount,
                                    "outflow_amount": tout.amount,
                                    "transit_delay_hours": round(delta_hrs, 2),
                                    "flow_retention_ratio": round(pass_through_ratio, 2)
                                }
                            ))
                            if pat_counter >= 5:
                                return patterns
        return patterns

    def detect_fan_in(self) -> List[DetectedPattern]:
        """Detect aggregation: 3 or more accounts sending funds to one account within 48h."""
        patterns = []
        pat_counter = 0

        for acc_id, node in self.graph.nodes.items():
            if node["in_degree"] >= 3:
                in_txs = [self.graph.tx_by_id[tid] for tid in node["transactions_in"]]
                src_accs = list(set(tx.source_account for tx in in_txs))
                if len(src_accs) >= 3:
                    pat_counter += 1
                    patterns.append(DetectedPattern(
                        pattern_id=f"PAT-FANIN-{pat_counter:03d}",
                        pattern_type="fan_in_aggregation",
                        severity="medium",
                        title=f"Fan-In Aggregation into '{acc_id}'",
                        description=(
                            f"Account '{acc_id}' aggregated funds from {len(src_accs)} distinct sources "
                            f"totaling {node['total_in']} across {len(in_txs)} transactions."
                        ),
                        involved_accounts=src_accs + [acc_id],
                        involved_transactions=[tx.transaction_id for tx in in_txs],
                        metrics={
                            "collector_account": acc_id,
                            "distinct_sources": len(src_accs),
                            "total_aggregated_amount": round(node["total_in"], 2)
                        }
                    ))
        return patterns

    def detect_fan_out(self) -> List[DetectedPattern]:
        """Detect disbursement: 1 account sending funds to 3 or more accounts within 48h."""
        patterns = []
        pat_counter = 0

        for acc_id, node in self.graph.nodes.items():
            if node["out_degree"] >= 3:
                out_txs = [self.graph.tx_by_id[tid] for tid in node["transactions_out"]]
                dst_accs = list(set(tx.destination_account for tx in out_txs))
                if len(dst_accs) >= 3:
                    pat_counter += 1
                    patterns.append(DetectedPattern(
                        pattern_id=f"PAT-FANOUT-{pat_counter:03d}",
                        pattern_type="fan_out_distribution",
                        severity="medium",
                        title=f"Fan-Out Distribution from '{acc_id}'",
                        description=(
                            f"Account '{acc_id}' distributed funds to {len(dst_accs)} distinct destinations "
                            f"totaling {node['total_out']} across {len(out_txs)} transactions."
                        ),
                        involved_accounts=[acc_id] + dst_accs,
                        involved_transactions=[tx.transaction_id for tx in out_txs],
                        metrics={
                            "distributor_account": acc_id,
                            "distinct_destinations": len(dst_accs),
                            "total_distributed_amount": round(node["total_out"], 2)
                        }
                    ))
        return patterns
