"""
RingTrace: Temporal Transaction Graph Engine
Pure Python implementation of a time-respecting directed financial transaction graph.
Preserves strict chronological ordering, edge attributes, and path constraints.
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import datetime, timezone
from collections import defaultdict
import hashlib
from backend.models.schemas import Transaction, AccountNode, GraphPath


def parse_iso(ts_str: str) -> datetime:
    """Safely parse ISO timestamp string into a timezone-aware UTC datetime."""
    clean_str = ts_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        raise ValueError(f"Invalid timestamp format '{ts_str}': {e}")


class TemporalTransactionGraph:
    """
    Time-aware directed graph representing accounts (nodes) and transactions (edges).
    Enforces that valid flows must respect causal time order (t_i <= t_{i+1}).
    """

    def __init__(self, transactions: List[Transaction]):
        self.raw_transactions = transactions
        self.nodes: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "in_degree": 0,
            "out_degree": 0,
            "total_in": 0.0,
            "total_out": 0.0,
            "transactions_in": [],
            "transactions_out": [],
            "first_seen": None,
            "last_seen": None
        })
        self.adjacency: Dict[str, List[Transaction]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[Transaction]] = defaultdict(list)
        self.tx_by_id: Dict[str, Transaction] = {}
        
        self._build_graph()

    def _build_graph(self):
        """Construct the adjacency lists and compute account-level properties."""
        for tx in self.raw_transactions:
            self.tx_by_id[tx.transaction_id] = tx
            src = tx.source_account
            dst = tx.destination_account
            tx_time = parse_iso(tx.timestamp)
            
            # Record edges
            self.adjacency[src].append(tx)
            self.reverse_adjacency[dst].append(tx)
            
            # Update source stats
            src_node = self.nodes[src]
            src_node["out_degree"] += 1
            src_node["total_out"] += tx.amount
            src_node["transactions_out"].append(tx.transaction_id)
            if src_node["first_seen"] is None or tx_time < src_node["first_seen"]:
                src_node["first_seen"] = tx_time
            if src_node["last_seen"] is None or tx_time > src_node["last_seen"]:
                src_node["last_seen"] = tx_time
                
            # Update dest stats
            dst_node = self.nodes[dst]
            dst_node["in_degree"] += 1
            dst_node["total_in"] += tx.amount
            dst_node["transactions_in"].append(tx.transaction_id)
            if dst_node["first_seen"] is None or tx_time < dst_node["first_seen"]:
                dst_node["first_seen"] = tx_time
            if dst_node["last_seen"] is None or tx_time > dst_node["last_seen"]:
                dst_node["last_seen"] = tx_time

        # Sort outgoing edges by timestamp for time-respecting searches
        for src in self.adjacency:
            self.adjacency[src].sort(key=lambda x: parse_iso(x.timestamp))

    def get_account_nodes(self) -> List[AccountNode]:
        """Convert internal node stats to validated AccountNode schemas."""
        account_nodes = []
        for acc_id, stats in self.nodes.items():
            first_s = stats["first_seen"].isoformat() if stats["first_seen"] else None
            last_s = stats["last_seen"].isoformat() if stats["last_seen"] else None
            
            # Simple heuristic classification of account type for evidence pack
            in_deg = stats["in_degree"]
            out_deg = stats["out_degree"]
            if in_deg >= 4 and out_deg <= 1:
                acc_type = "aggregator_sink"
            elif out_deg >= 4 and in_deg <= 1:
                acc_type = "disbursement_source"
            elif in_deg >= 1 and out_deg >= 1:
                acc_type = "intermediary"
            else:
                acc_type = "individual"

            account_nodes.append(AccountNode(
                account_id=acc_id,
                account_type=acc_type,
                declared_purpose=None,  # Not present in synthetic transactions (flagged as unknown)
                risk_tier="elevated" if (in_deg + out_deg > 5) else "standard",
                first_seen=first_s,
                last_seen=last_s
            ))
        return account_nodes

    def find_time_respecting_paths(
        self, 
        max_hops: int = 6, 
        max_window_hours: float = 72.0
    ) -> List[GraphPath]:
        """
        DFS to discover all valid directed paths where transactions occur in chronological order:
        t(tx_0) <= t(tx_1) <= ... <= t(tx_k) within max_window_hours.
        """
        discovered_paths: List[GraphPath] = []
        path_counter = 0

        def dfs(
            current_acc: str, 
            visited_accs: List[str], 
            visited_txs: List[Transaction]
        ):
            nonlocal path_counter
            if len(visited_txs) >= 2:
                # Valid multi-hop path candidate
                t_start = parse_iso(visited_txs[0].timestamp)
                t_end = parse_iso(visited_txs[-1].timestamp)
                duration_hrs = max(0.01, (t_end - t_start).total_seconds() / 3600.0)
                tot_amt = sum(tx.amount for tx in visited_txs)
                
                path_counter += 1
                discovered_paths.append(GraphPath(
                    path_id=f"PATH-{path_counter:03d}",
                    accounts=list(visited_accs),
                    transaction_ids=[t.transaction_id for t in visited_txs],
                    start_time=visited_txs[0].timestamp,
                    end_time=visited_txs[-1].timestamp,
                    total_duration_hours=round(duration_hrs, 2),
                    total_amount=round(tot_amt, 2),
                    is_chronological=True,
                    hop_count=len(visited_txs),
                    velocity_rate=round(tot_amt / duration_hrs, 2)
                ))

            if len(visited_txs) >= max_hops:
                return

            last_time = parse_iso(visited_txs[-1].timestamp) if visited_txs else None
            start_time = parse_iso(visited_txs[0].timestamp) if visited_txs else None

            for next_tx in self.adjacency[current_acc]:
                next_time = parse_iso(next_tx.timestamp)
                
                # Check chronological constraint
                if last_time and next_time < last_time:
                    continue  # Violates causal time ordering
                
                # Check max time window from origin
                if start_time and (next_time - start_time).total_seconds() / 3600.0 > max_window_hours:
                    continue
                
                next_acc = next_tx.destination_account
                # Avoid simple loops in basic paths (cycles are handled separately)
                if next_acc in visited_accs:
                    continue

                visited_accs.append(next_acc)
                visited_txs.append(next_tx)
                dfs(next_acc, visited_accs, visited_txs)
                visited_txs.pop()
                visited_accs.pop()

        # Run DFS from accounts that have outgoing transactions
        for start_acc in list(self.adjacency.keys()):
            for first_tx in self.adjacency[start_acc]:
                dfs(
                    first_tx.destination_account, 
                    [start_acc, first_tx.destination_account], 
                    [first_tx]
                )

        return discovered_paths

    def find_temporal_cycles(self, max_hops: int = 6) -> List[Dict[str, Any]]:
        """
        Find circular flows where funds return to an earlier account in the chain
        in strict chronological sequence: A -> B -> ... -> A.
        """
        cycles = []
        cycle_idx = 0

        def cycle_dfs(
            start_acc: str, 
            curr_acc: str, 
            visited_accs: List[str], 
            visited_txs: List[Transaction]
        ):
            nonlocal cycle_idx
            if len(visited_txs) > max_hops:
                return

            last_time = parse_iso(visited_txs[-1].timestamp) if visited_txs else None

            for next_tx in self.adjacency[curr_acc]:
                next_time = parse_iso(next_tx.timestamp)
                if last_time and next_time < last_time:
                    continue  # Time constraint violated

                next_acc = next_tx.destination_account

                if next_acc == start_acc and len(visited_txs) >= 2:
                    # Completed cycle
                    all_txs = visited_txs + [next_tx]
                    t_start = parse_iso(all_txs[0].timestamp)
                    t_end = parse_iso(all_txs[-1].timestamp)
                    duration_hrs = max(0.01, (t_end - t_start).total_seconds() / 3600.0)
                    cycle_idx += 1
                    cycles.append({
                        "cycle_id": f"CYC-{cycle_idx:03d}",
                        "accounts": visited_accs + [start_acc],
                        "transaction_ids": [t.transaction_id for t in all_txs],
                        "amounts": [t.amount for t in all_txs],
                        "duration_hours": round(duration_hrs, 2),
                        "start_time": all_txs[0].timestamp,
                        "end_time": all_txs[-1].timestamp,
                        "hop_count": len(all_txs)
                    })
                    continue

                if next_acc not in visited_accs:
                    visited_accs.append(next_acc)
                    visited_txs.append(next_tx)
                    cycle_dfs(start_acc, next_acc, visited_accs, visited_txs)
                    visited_txs.pop()
                    visited_accs.pop()

        for origin_acc in list(self.adjacency.keys()):
            for first_tx in self.adjacency[origin_acc]:
                cycle_dfs(
                    origin_acc, 
                    first_tx.destination_account, 
                    [origin_acc, first_tx.destination_account], 
                    [first_tx]
                )

        # De-duplicate cycles that share the exact set of transactions
        unique_cycles = []
        seen_tx_sets = set()
        for c in cycles:
            tx_key = tuple(sorted(c["transaction_ids"]))
            if tx_key not in seen_tx_sets:
                seen_tx_sets.add(tx_key)
                unique_cycles.append(c)

        return unique_cycles
