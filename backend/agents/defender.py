"""
RingTrace: Defender / Alternative-Hypothesis Challenger
Actively queries case data through controlled read-only tools to discover evidence
supporting legitimate business or personal explanations.
Guardrail: Cannot invent facts, jobs, salaries, or customer intent.
"""

from typing import List, Dict, Any, Tuple
import time
from backend.models.schemas import EvidencePack, StructuredClaim, ToolCallRecord, Transaction


class DefenderAgent:
    """
    Executes bounded, read-only tools against the evidence pack.
    Constructs counter-claims if supported by evidence; reports absence if unverified.
    """

    def __init__(self, evidence_pack: EvidencePack):
        self.evidence_pack = evidence_pack
        self.transactions = evidence_pack.transactions
        self.tool_call_records: List[ToolCallRecord] = []

    def execute_read_only_tools(self) -> Tuple[List[StructuredClaim], List[ToolCallRecord]]:
        """Executes authorized read-only investigation queries."""
        claims: List[StructuredClaim] = []
        claim_idx = 0

        # Tool 1: Search for recurring identical amounts (e.g. monthly subscriptions, payroll)
        t0 = time.time()
        recurring_records = self._tool_find_recurring_amounts()
        t_exec = (time.time() - t0) * 1000.0

        self.tool_call_records.append(ToolCallRecord(
            tool_id="TOOL-CALL-001",
            tool_name="search_recurring_amounts",
            agent_role="defender",
            query_params={"min_occurrences": 2},
            matched_record_ids=[t.transaction_id for t in recurring_records],
            execution_time_ms=round(t_exec, 2),
            timestamp=self.evidence_pack.frozen_at
        ))

        if recurring_records:
            claim_idx += 1
            sample_tx = recurring_records[0]
            matching_ids = [t.transaction_id for t in recurring_records[:4]]
            claims.append(StructuredClaim(
                claim_id=f"CLM-DEF-{claim_idx:03d}",
                agent_role="defender",
                claim_type="recurring_flow",
                statement=(
                    f"Evidence of recurring identical transfer value ({sample_tx.amount} {sample_tx.currency}) "
                    f"identified across {len(recurring_records)} transactions. Plausibly consistent with recurring "
                    f"vendor invoice, monthly retainer, or scheduled corporate settlement."
                ),
                transaction_ids=matching_ids,
                supporting_evidence_ids=["TOOL-CALL-001"],
                confidence_label="provisional",
                unknowns=["vendor_agreement_contract"],
                is_interpretation=True,
                validation_status="pending"
            ))

        # Tool 2: Search for commercial and payroll keywords in transaction memos
        t0 = time.time()
        memo_records = self._tool_find_commercial_memos()
        t_exec = (time.time() - t0) * 1000.0

        self.tool_call_records.append(ToolCallRecord(
            tool_id="TOOL-CALL-002",
            tool_name="search_commercial_memos",
            agent_role="defender",
            query_params={"keywords": ["invoice", "payroll", "salary", "vendor", "dividend", "settlement"]},
            matched_record_ids=[t.transaction_id for t in memo_records],
            execution_time_ms=round(t_exec, 2),
            timestamp=self.evidence_pack.frozen_at
        ))

        if memo_records:
            claim_idx += 1
            claims.append(StructuredClaim(
                claim_id=f"CLM-DEF-{claim_idx:03d}",
                agent_role="defender",
                claim_type="commercial_context",
                statement=(
                    f"Found {len(memo_records)} transactions with commercial descriptions "
                    f"('{memo_records[0].narrative_memo}'). Indicates legitimate transactional pretext "
                    f"that must be verified before concluding criminal structuring."
                ),
                transaction_ids=[t.transaction_id for t in memo_records[:3]],
                supporting_evidence_ids=["TOOL-CALL-002"],
                confidence_label="provisional",
                unknowns=["tax_invoice_verification"],
                is_interpretation=True,
                validation_status="pending"
            ))

        # Tool 3: Query account connectivity and fan-out distribution
        t0 = time.time()
        merchants = [a for a in self.evidence_pack.accounts if a.account_type in ["aggregator_sink", "disbursement_source"]]
        t_exec = (time.time() - t0) * 1000.0

        self.tool_call_records.append(ToolCallRecord(
            tool_id="TOOL-CALL-003",
            tool_name="query_account_archetype",
            agent_role="defender",
            query_params={"archetypes": ["aggregator_sink", "disbursement_source"]},
            matched_record_ids=[a.account_id for a in merchants],
            execution_time_ms=round(t_exec, 2),
            timestamp=self.evidence_pack.frozen_at
        ))

        if merchants:
            claim_idx += 1
            claims.append(StructuredClaim(
                claim_id=f"CLM-DEF-{claim_idx:03d}",
                agent_role="defender",
                claim_type="account_profile_observation",
                statement=(
                    f"Identified entity '{merchants[0].account_id}' exhibiting high fan-in/fan-out connectivity. "
                    f"Such patterns are common in payment gateways, e-commerce merchants, and payroll clearinghouses."
                ),
                transaction_ids=[],
                supporting_evidence_ids=["TOOL-CALL-003"],
                confidence_label="provisional",
                unknowns=["merchant_license_registry"],
                is_interpretation=True,
                validation_status="pending"
            ))

        # Guardrail: If no alternative evidence was discovered, state this transparently!
        if not claims:
            claim_idx += 1
            claims.append(StructuredClaim(
                claim_id=f"CLM-DEF-{claim_idx:03d}",
                agent_role="defender",
                claim_type="gap_observation",
                statement=(
                    "Read-only query executed: No recurring amounts, commercial memos, or registered merchant "
                    "profiles found in available records. Plausible legitimate explanation cannot be substantiated "
                    "with supplied transaction records alone."
                ),
                transaction_ids=[],
                supporting_evidence_ids=[],
                confidence_label="verified",
                unknowns=["customer_invoicing_records", "account_purpose"],
                is_interpretation=False,
                validation_status="pending"
            ))

        return claims, self.tool_call_records

    def _tool_find_recurring_amounts(self) -> List[Transaction]:
        """Tool implementation: Finds transactions that repeat the exact same amount."""
        amount_counts: Dict[float, List[Transaction]] = {}
        for t in self.transactions:
            amount_counts.setdefault(t.amount, []).append(t)
        
        matches = []
        for amt, tx_list in amount_counts.items():
            if len(tx_list) >= 2:
                matches.extend(tx_list)
        return matches

    def _tool_find_commercial_memos(self) -> List[Transaction]:
        """Tool implementation: Scans narrative memos for legitimate commercial indicators."""
        keywords = ["invoice", "payroll", "salary", "vendor", "dividend", "settlement", "rent"]
        matches = []
        for t in self.transactions:
            if t.narrative_memo:
                memo_lower = t.narrative_memo.lower()
                if any(kw in memo_lower for kw in keywords):
                    matches.append(t)
        return matches
