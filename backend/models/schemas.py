"""
RingTrace: Pydantic Data Contracts and Canonical Schemas
Strict data contracts for transactions, evidence packs, claims, stress tests, and CERP.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Canonical transaction schema as required by Section 25.3"""
    transaction_id: str
    timestamp: str  # ISO-8601 string, e.g., '2026-01-01T10:15:00Z'
    source_account: str
    destination_account: str
    amount: float
    currency: str = "INR"
    transaction_type: str = "transfer"  # transfer, payout, deposit, card_payment
    source_record_id: str
    narrative_memo: Optional[str] = None
    is_planted_defect: bool = False
    defect_description: Optional[str] = None


class AccountNode(BaseModel):
    """Account node representing participants in the transaction network"""
    account_id: str
    account_type: str = "individual"  # individual, merchant, payroll_entity, intermediary
    declared_purpose: Optional[str] = None  # None represents missing/unknown context
    risk_tier: str = "standard"
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class GraphPath(BaseModel):
    """A directed, time-respecting path of funds between accounts"""
    path_id: str
    accounts: List[str]
    transaction_ids: List[str]
    start_time: str
    end_time: str
    total_duration_hours: float
    total_amount: float
    is_chronological: bool
    hop_count: int
    velocity_rate: float  # amount / duration


class DetectedPattern(BaseModel):
    """Typology or flow indicator detected in the transaction graph"""
    pattern_id: str
    pattern_type: str  # cycle_ring, multi_hop_layering, fan_in_aggregation, fan_out_distribution, rapid_pass_through
    severity: str = "medium"  # low, medium, high
    title: str
    description: str
    involved_accounts: List[str]
    involved_transactions: List[str]
    metrics: Dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    """Frozen, immutable snapshot of evidence and computed features"""
    case_id: str
    dataset_version: str
    frozen_at: str
    transactions: List[Transaction]
    accounts: List[AccountNode]
    patterns: List[DetectedPattern]
    paths: List[GraphPath]
    calculated_metrics: Dict[str, Any]
    missing_fields: List[str] = Field(default_factory=list)
    provenance_hash: str


class StructuredClaim(BaseModel):
    """Structured claim contract (Section 25.4) ensuring factual traceability"""
    claim_id: str
    agent_role: str  # planner, prosecutor, defender, reconciler
    claim_type: str  # temporal_observation, rapid_pass_through, recurring_flow, contradiction_flag, gap_flag
    statement: str
    transaction_ids: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    counter_evidence_ids: List[str] = Field(default_factory=list)
    confidence_label: str = "provisional"  # provisional, verified, challenged, unverified
    unknowns: List[str] = Field(default_factory=list)
    is_interpretation: bool = False  # False = factual statement; True = subjective interpretation
    validation_status: str = "pending"  # pending, verified, rejected, flagged
    rejection_reason: Optional[str] = None
    validation_notes: Optional[str] = None


class ToolCallRecord(BaseModel):
    """Audit record for read-only evidence retrieval tools"""
    tool_id: str
    tool_name: str
    agent_role: str
    query_params: Dict[str, Any]
    matched_record_ids: List[str]
    execution_time_ms: float
    timestamp: str


class StressTestResult(BaseModel):
    """Result of one of the 5 case-level evidence stress tests"""
    test_id: str
    test_name: str  # provenance_integrity, temporal_consistency, competing_hypotheses, contradictions_and_gaps, pivotal_sensitivity
    status: str  # PASSED, CHALLENGED, FAILED, SENSITIVE
    description: str
    checked_count: int
    passed_count: int
    failed_count: int
    findings: List[str] = Field(default_factory=list)
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    pivotal_transaction_id: Optional[str] = None
    sensitivity_impact: Optional[Dict[str, Any]] = None


class CERPReport(BaseModel):
    """Case Evidence Robustness Profile (CERP) contract (Section 25.6)"""
    case_id: str
    generated_at: str
    synthetic_data_notice: str = "SYNTHETIC TRANSACTION CASE — FOR INVESTIGATION DECISION SUPPORT ONLY"
    
    # 5 Key Dimensions
    provenance_status: str  # VERIFIED, COMPROMISED
    chronology_status: str  # VERIFIED, VIOLATED
    graph_path_status: str  # VALID, BROKEN
    
    suspicious_hypothesis: str
    suspicious_hypothesis_status: str  # SUPPORTED, WEAKENED, UNVERIFIED
    supporting_records: List[str]
    
    alternative_hypothesis: Optional[str] = None
    alternative_hypothesis_status: str  # PLAUSIBLE, NO_SUPPORT_FOUND, INSUFFICIENT_DATA
    counter_records: List[str] = Field(default_factory=list)
    
    contradictions: List[str] = Field(default_factory=list)
    missing_context_unknowns: List[str] = Field(default_factory=list)
    
    pivotal_dependency: Optional[str] = None
    sensitivity_result: str
    
    suggested_workflow_status: str  # ESCALATE_FOR_HUMAN_REVIEW, CLOSURE_REVIEW, INSUFFICIENT_EVIDENCE, REQUEST_MORE_INFORMATION
    workflow_explanation: str
    
    human_review_status: str = "PENDING_ANALYST_ACTION"
    human_analyst_decision: Optional[str] = None
    human_analyst_notes: Optional[str] = None
    reviewed_at: Optional[str] = None


class AuditEvent(BaseModel):
    """Append-only audit trail event"""
    event_id: str
    case_id: str
    timestamp: str
    actor: str  # system, planner, prosecutor, defender, stress_engine, reconciler, analyst
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)


class InvestigationRunResult(BaseModel):
    """Complete result of a bounded investigation run"""
    case_id: str
    evidence_pack: EvidencePack
    planner_plan: Dict[str, Any]
    prosecutor_claims: List[StructuredClaim]
    defender_claims: List[StructuredClaim]
    defender_tool_calls: List[ToolCallRecord]
    stress_test_results: List[StressTestResult]
    rejected_claims: List[StructuredClaim]
    reconciler_summary: Dict[str, Any]
    cerp: CERPReport
    audit_events: List[AuditEvent]
