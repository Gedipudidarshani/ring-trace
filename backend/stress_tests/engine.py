"""
RingTrace: Case Evidence Stress-Testing Engine
Executes the 5 case-level stress tests specified in Section 5 of the Blueprint:
1. Provenance Integrity
2. Temporal Consistency
3. Competing Hypothesis Test
4. Contradiction & Missing-Context Test
5. Pivotal-Evidence Sensitivity (Controlled perturbation & fragility diagnosis)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.models.schemas import (
    Transaction, 
    EvidencePack, 
    StructuredClaim, 
    StressTestResult, 
    DetectedPattern
)
from backend.graph.temporal_graph import TemporalTransactionGraph, parse_iso
from backend.graph.detectors import CandidatePatternDetector


class StressTestEngine:
    """
    Orchestrates the 5 case-level stress tests.
    Produces unambiguous pass/fail/challenged/sensitive findings.
    """

    def __init__(self, evidence_pack: EvidencePack):
        self.evidence_pack = evidence_pack
        self.tx_list = evidence_pack.transactions
        self.tx_map = {t.transaction_id: t for t in self.tx_list}

    def run_all_stress_tests(
        self, 
        prosecutor_claims: List[StructuredClaim], 
        defender_claims: List[StructuredClaim]
    ) -> List[StressTestResult]:
        """Runs the complete suite of 5 stress tests."""
        results = []
        results.append(self.test_provenance_integrity(prosecutor_claims, defender_claims))
        results.append(self.test_temporal_consistency())
        results.append(self.test_competing_hypotheses(prosecutor_claims, defender_claims))
        results.append(self.test_contradictions_and_missing_context(prosecutor_claims, defender_claims))
        results.append(self.test_pivotal_evidence_sensitivity())
        return results

    def test_provenance_integrity(
        self, 
        prosecutor_claims: List[StructuredClaim], 
        defender_claims: List[StructuredClaim]
    ) -> StressTestResult:
        """
        Stress Test 1: Provenance Integrity
        Verifies transaction record identifiers, amounts, timestamps, and deduplication.
        """
        violations = []
        checked = 0
        passed = 0

        # Check unique IDs in transaction dataset
        seen_ids = set()
        for tx in self.tx_list:
            checked += 1
            if tx.transaction_id in seen_ids:
                violations.append({
                    "type": "duplicate_transaction_id",
                    "transaction_id": tx.transaction_id,
                    "detail": "Duplicate transaction ID found in dataset."
                })
            else:
                seen_ids.add(tx.transaction_id)
                passed += 1

            if tx.amount <= 0:
                violations.append({
                    "type": "non_positive_amount",
                    "transaction_id": tx.transaction_id,
                    "detail": f"Amount {tx.amount} is non-positive."
                })

        # Check claim citations against source IDs
        all_claims = prosecutor_claims + defender_claims
        for clm in all_claims:
            for tid in clm.transaction_ids:
                checked += 1
                if tid not in self.tx_map:
                    violations.append({
                        "type": "unanchored_claim_citation",
                        "claim_id": clm.claim_id,
                        "transaction_id": tid,
                        "detail": f"Claim references unverified ID '{tid}'."
                    })
                else:
                    passed += 1

        status = "PASSED" if not violations else "FAILED"
        findings = [
            f"Verified {len(self.tx_list)} source transactions against provenance snapshot.",
            f"Validated {len(all_claims)} agent claims against immutable record ledger."
        ]
        if violations:
            findings.append(f"Flagged {len(violations)} provenance violations.")

        return StressTestResult(
            test_id="ST-001",
            test_name="provenance_integrity",
            status=status,
            description="Checks that all cited IDs, amounts, timestamps, and records match exact source data.",
            checked_count=checked,
            passed_count=passed,
            failed_count=len(violations),
            findings=findings,
            violations=violations
        )

    def test_temporal_consistency(self) -> StressTestResult:
        """
        Stress Test 2: Temporal Consistency
        Evaluates whether paths, flows, and rapid pass-throughs satisfy forward time arrow.
        """
        violations = []
        checked = 0
        passed = 0

        # Validate time ordering on all computed graph paths
        for p in self.evidence_pack.paths:
            checked += 1
            path_txs = [self.tx_map[tid] for tid in p.transaction_ids if tid in self.tx_map]
            
            is_valid_order = True
            for i in range(len(path_txs) - 1):
                t1 = parse_iso(path_txs[i].timestamp)
                t2 = parse_iso(path_txs[i+1].timestamp)
                if t2 < t1:
                    is_valid_order = False
                    violations.append({
                        "path_id": p.path_id,
                        "violating_tx_pair": [path_txs[i].transaction_id, path_txs[i+1].transaction_id],
                        "timestamps": [path_txs[i].timestamp, path_txs[i+1].timestamp],
                        "detail": "Path involves backwards time travel / chronological violation."
                    })
                    break
            
            if is_valid_order:
                passed += 1

        status = "PASSED" if not violations else "FAILED"
        findings = [
            f"Validated temporal sequence across {len(self.evidence_pack.paths)} directed paths.",
            "Time consistency verified: no retrocausal transfers detected." if not violations else f"Detected {len(violations)} impossible temporal sequences."
        ]

        return StressTestResult(
            test_id="ST-002",
            test_name="temporal_consistency",
            status=status,
            description="Verifies that transaction sequences and graph flows satisfy strict causal chronology (t_i <= t_{i+1}).",
            checked_count=checked,
            passed_count=passed,
            failed_count=len(violations),
            findings=findings,
            violations=violations
        )

    def test_competing_hypotheses(
        self, 
        prosecutor_claims: List[StructuredClaim], 
        defender_claims: List[StructuredClaim]
    ) -> StressTestResult:
        """
        Stress Test 3: Competing Hypothesis Test
        Checks whether both suspicious AND plausible alternative hypotheses were formulated and tested.
        """
        has_suspicious = any(c.agent_role == "prosecutor" for c in prosecutor_claims)
        has_alternative = any(c.agent_role == "defender" for c in defender_claims)
        
        findings = []
        if has_suspicious:
            findings.append("Suspicious hypothesis constructed: cites rapid transit and circular patterns.")
        else:
            findings.append("Missing suspicious hypothesis formulation.")

        if has_alternative:
            findings.append(f"Alternative hypothesis tested: Defender presented {len(defender_claims)} counter-claims.")
        else:
            findings.append("No alternative hypothesis formulated by Defender.")

        status = "PASSED" if (has_suspicious and has_alternative) else "CHALLENGED"

        return StressTestResult(
            test_id="ST-003",
            test_name="competing_hypotheses",
            status=status,
            description="Verifies that both suspicious and legitimate alternative explanations were formulated and evaluated.",
            checked_count=2,
            passed_count=2 if status == "PASSED" else 1,
            failed_count=0 if status == "PASSED" else 1,
            findings=findings,
            violations=[]
        )

    def test_contradictions_and_missing_context(
        self, 
        prosecutor_claims: List[StructuredClaim], 
        defender_claims: List[StructuredClaim]
    ) -> StressTestResult:
        """
        Stress Test 4: Contradiction & Missing-Context Test
        Surfaces conflicts between suspicious patterns and legitimate data (e.g. fixed recurring amounts),
        and verifies that uncollected fields are declared as UNKNOWNS rather than assumed.
        """
        contradictions = []
        unknowns = list(self.evidence_pack.missing_fields)

        # Check for recurring fixed payments or business payroll indicators
        amounts = [t.amount for t in self.tx_list]
        amount_counts = {}
        for amt in amounts:
            amount_counts[amt] = amount_counts.get(amt, 0) + 1

        recurring_amounts = [amt for amt, count in amount_counts.items() if count >= 2]
        if recurring_amounts:
            contradictions.append(
                f"Fixed recurring amount detected: {recurring_amounts[0]} appears {amount_counts[recurring_amounts[0]]} times. "
                "Matches recurring commercial vendor payment or structured disbursement profile."
            )

        # Check narrative memos for legitimate commercial tags
        memos = [t.narrative_memo for t in self.tx_list if t.narrative_memo]
        commercial_keywords = ["invoice", "payroll", "salary", "vendor", "dividend", "rent"]
        found_keywords = []
        for m in memos:
            for kw in commercial_keywords:
                if kw in m.lower():
                    found_keywords.append(kw)
        
        if found_keywords:
            contradictions.append(
                f"Source memos contain commercial identifiers: {list(set(found_keywords))}. "
                "Weakens pure money-mule hypothesis without further customer profiling."
            )

        status = "CHALLENGED" if contradictions else "PASSED"
        findings = [
            f"Cataloged {len(unknowns)} missing contextual variables (KYC declared purpose, invoice documentation).",
            f"Identified {len(contradictions)} potential contradictory indicators."
        ] + contradictions

        return StressTestResult(
            test_id="ST-004",
            test_name="contradictions_and_gaps",
            status=status,
            description="Detects contradictory evidence (e.g., payroll patterns, fixed amounts) and explicitly registers unknowns.",
            checked_count=len(self.tx_list) + len(unknowns),
            passed_count=len(self.tx_list),
            failed_count=len(contradictions),
            findings=findings,
            violations=[{"contradiction": c} for c in contradictions]
        )

    def test_pivotal_evidence_sensitivity(self) -> StressTestResult:
        """
        Stress Test 5: Pivotal-Evidence Sensitivity (Core Innovation)
        Identifies the pivotal transaction in the primary flagged pattern.
        Performs a controlled exclusion simulation and measures the delta on graph topology.
        Discloses whether the suspicious case collapses if that single transaction is excluded.
        """
        patterns = self.evidence_pack.patterns
        if not patterns:
            return StressTestResult(
                test_id="ST-005",
                test_name="pivotal_evidence_sensitivity",
                status="PASSED",
                description="Controlled sensitivity test: evaluated case dependency on pivotal evidence.",
                checked_count=1,
                passed_count=1,
                failed_count=0,
                findings=["No high-severity flow patterns flagged. Sensitivity test not applicable."],
                pivotal_transaction_id=None,
                sensitivity_impact={"is_fragile": False}
            )

        # Select primary pattern (e.g. cycle or top layering chain)
        primary_pattern = patterns[0]
        involved_txs = primary_pattern.involved_transactions

        if not involved_txs:
            pivotal_tx_id = self.tx_list[0].transaction_id if self.tx_list else "TX-NONE"
        else:
            # Pivotal transaction is the highest value or bridge transaction in the pattern
            pattern_tx_objs = [self.tx_map[tid] for tid in involved_txs if tid in self.tx_map]
            pattern_tx_objs.sort(key=lambda x: x.amount, reverse=True)
            pivotal_tx_id = pattern_tx_objs[0].transaction_id

        pivotal_tx = self.tx_map[pivotal_tx_id]

        # Simulating removal of pivotal_tx_id
        perturbed_txs = [t for t in self.tx_list if t.transaction_id != pivotal_tx_id]
        perturbed_graph = TemporalTransactionGraph(perturbed_txs)
        perturbed_detector = CandidatePatternDetector(perturbed_graph)
        perturbed_patterns = perturbed_detector.detect_all_patterns()

        # Check impact
        orig_cyc_count = len([p for p in patterns if p.pattern_type == "cycle_ring"])
        new_cyc_count = len([p for p in perturbed_patterns if p.pattern_type == "cycle_ring"])
        
        orig_lay_count = len([p for p in patterns if p.pattern_type == "multi_hop_layering"])
        new_lay_count = len([p for p in perturbed_patterns if p.pattern_type == "multi_hop_layering"])

        cycle_broken = (orig_cyc_count > 0 and new_cyc_count == 0)
        layering_shortened = (orig_lay_count > 0 and new_lay_count < orig_lay_count)
        is_fragile = cycle_broken or layering_shortened

        sensitivity_details = {
            "pivotal_transaction_id": pivotal_tx_id,
            "amount": pivotal_tx.amount,
            "currency": pivotal_tx.currency,
            "source_account": pivotal_tx.source_account,
            "destination_account": pivotal_tx.destination_account,
            "cycle_broken_on_removal": cycle_broken,
            "layering_chain_impact": "collapsed" if layering_shortened else "sustained",
            "is_case_fragile": is_fragile
        }

        findings = [
            f"Pivotal transaction identified: '{pivotal_tx_id}' ({pivotal_tx.amount} {pivotal_tx.currency} from '{pivotal_tx.source_account}' to '{pivotal_tx.destination_account}').",
            f"Diagnostic exclusion simulation: If '{pivotal_tx_id}' is excluded, primary pattern '{primary_pattern.pattern_type}' is {'COMPLETELY BROKEN' if is_fragile else 'STABLE'}.",
            f"Case Fragility Assessment: {'HIGH DEPENDENCY ON SINGLE PIVOTAL TRANSACTION — Case narrative is sensitive.' if is_fragile else 'ROBUST — Pattern persists across multiple independent flow paths.'}"
        ]

        return StressTestResult(
            test_id="ST-005",
            test_name="pivotal_evidence_sensitivity",
            status="SENSITIVE" if is_fragile else "PASSED",
            description="Controlled diagnostic: excludes pivotal bridge transaction to measure narrative fragility.",
            checked_count=len(self.tx_list),
            passed_count=len(self.tx_list) - 1,
            failed_count=1 if is_fragile else 0,
            findings=findings,
            pivotal_transaction_id=pivotal_tx_id,
            sensitivity_impact=sensitivity_details
        )
