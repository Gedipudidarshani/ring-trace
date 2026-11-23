"""
RingTrace: Curated Synthetic AML Scenarios
Provides benchmark scenarios with verified ground truth:
1. Circular Layering Ring (Mule network with pivotal bridge transaction)
2. Payroll False Positive (High fan-out with recurring fixed commercial disbursements)
3. Smurfing Aggregation (Fan-in followed by rapid exit)
4. Planted Defect Scenario (Fabricated IDs, impossible timestamps, corrupted amounts)
"""

from typing import List, Dict, Any
from backend.models.schemas import Transaction


def get_case_mule_ring() -> List[Transaction]:
    """
    Scenario 1: Circular Layering Ring (RT-1042)
    Funds circulate sequentially through 5 accounts in 24 hours.
    TX-RING-004 is the pivotal bridge transaction returning funds to origin.
    """
    return [
        Transaction(
            transaction_id="TX-RING-001",
            timestamp="2026-11-20T08:00:00Z",
            source_account="ACC-ORIGIN-01",
            destination_account="ACC-LAYER-02",
            amount=485000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-1001",
            narrative_memo="Funds transfer - urgent"
        ),
        Transaction(
            transaction_id="TX-RING-002",
            timestamp="2026-11-20T11:15:00Z",
            source_account="ACC-LAYER-02",
            destination_account="ACC-LAYER-03",
            amount=472000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-1002",
            narrative_memo="Settlement trf"
        ),
        Transaction(
            transaction_id="TX-RING-003",
            timestamp="2026-11-20T14:45:00Z",
            source_account="ACC-LAYER-03",
            destination_account="ACC-LAYER-04",
            amount=468000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-1003",
            narrative_memo="Internal balance rebalance"
        ),
        Transaction(
            transaction_id="TX-RING-004",  # PIVOTAL BRIDGE TRANSACTION
            timestamp="2026-11-20T18:30:00Z",
            source_account="ACC-LAYER-04",
            destination_account="ACC-LAYER-05",
            amount=460000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-1004",
            narrative_memo="Bridge remittance"
        ),
        Transaction(
            transaction_id="TX-RING-005",
            timestamp="2026-11-21T06:00:00Z",
            source_account="ACC-LAYER-05",
            destination_account="ACC-ORIGIN-01",  # Completes cycle
            amount=455000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-1005",
            narrative_memo="Return of advance"
        )
    ]


def get_case_payroll_false_positive() -> List[Transaction]:
    """
    Scenario 2: Commercial Payroll (RT-2091)
    High volume fan-out disbursement resembling layering, but with recurring fixed
    amounts and corporate payroll descriptions. Defender should identify legitimate pretexts.
    """
    return [
        Transaction(
            transaction_id="TX-PAY-001",
            timestamp="2026-11-01T09:00:00Z",
            source_account="ACC-CORP-PARENT",
            destination_account="ACC-PAYROLL-DISBURSE",
            amount=270000.0,
            currency="INR",
            transaction_type="deposit",
            source_record_id="SRC-REC-2001",
            narrative_memo="Monthly corporate payroll funding - Nov 2026"
        ),
        Transaction(
            transaction_id="TX-PAY-002",
            timestamp="2026-11-01T10:00:00Z",
            source_account="ACC-PAYROLL-DISBURSE",
            destination_account="ACC-EMP-101",
            amount=45000.0,
            currency="INR",
            transaction_type="payout",
            source_record_id="SRC-REC-2002",
            narrative_memo="Salary for November 2026"
        ),
        Transaction(
            transaction_id="TX-PAY-003",
            timestamp="2026-11-01T10:02:00Z",
            source_account="ACC-PAYROLL-DISBURSE",
            destination_account="ACC-EMP-102",
            amount=45000.0,
            currency="INR",
            transaction_type="payout",
            source_record_id="SRC-REC-2003",
            narrative_memo="Salary for November 2026"
        ),
        Transaction(
            transaction_id="TX-PAY-004",
            timestamp="2026-11-01T10:05:00Z",
            source_account="ACC-PAYROLL-DISBURSE",
            destination_account="ACC-EMP-103",
            amount=45000.0,
            currency="INR",
            transaction_type="payout",
            source_record_id="SRC-REC-2004",
            narrative_memo="Salary for November 2026"
        ),
        Transaction(
            transaction_id="TX-PAY-005",
            timestamp="2026-11-01T10:07:00Z",
            source_account="ACC-PAYROLL-DISBURSE",
            destination_account="ACC-EMP-104",
            amount=45000.0,
            currency="INR",
            transaction_type="payout",
            source_record_id="SRC-REC-2005",
            narrative_memo="Salary for November 2026"
        ),
        Transaction(
            transaction_id="TX-PAY-006",
            timestamp="2026-11-01T10:10:00Z",
            source_account="ACC-PAYROLL-DISBURSE",
            destination_account="ACC-EMP-105",
            amount=45000.0,
            currency="INR",
            transaction_type="payout",
            source_record_id="SRC-REC-2006",
            narrative_memo="Salary for November 2026"
        ),
        Transaction(
            transaction_id="TX-PAY-007",
            timestamp="2026-11-01T10:12:00Z",
            source_account="ACC-PAYROLL-DISBURSE",
            destination_account="ACC-EMP-106",
            amount=45000.0,
            currency="INR",
            transaction_type="payout",
            source_record_id="SRC-REC-2007",
            narrative_memo="Salary for November 2026"
        )
    ]


def get_case_smurf_aggregation() -> List[Transaction]:
    """
    Scenario 3: Fan-In Aggregation (RT-3015)
    Multiple originator accounts transfer funds to one central mule account,
    which promptly transfers the total out to a foreign or crypto exchange intermediary.
    """
    return [
        Transaction(
            transaction_id="TX-SMURF-001",
            timestamp="2026-11-18T14:10:00Z",
            source_account="ACC-FEEDER-A",
            destination_account="ACC-MULE-COLLECTOR",
            amount=98000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-3001",
            narrative_memo="Instant P2P"
        ),
        Transaction(
            transaction_id="TX-SMURF-002",
            timestamp="2026-11-18T14:25:00Z",
            source_account="ACC-FEEDER-B",
            destination_account="ACC-MULE-COLLECTOR",
            amount=95000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-3002",
            narrative_memo="Instant P2P"
        ),
        Transaction(
            transaction_id="TX-SMURF-003",
            timestamp="2026-11-18T15:00:00Z",
            source_account="ACC-FEEDER-C",
            destination_account="ACC-MULE-COLLECTOR",
            amount=99000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-3003",
            narrative_memo="Payment"
        ),
        Transaction(
            transaction_id="TX-SMURF-004",
            timestamp="2026-11-18T15:30:00Z",
            source_account="ACC-FEEDER-D",
            destination_account="ACC-MULE-COLLECTOR",
            amount=94000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-3004",
            narrative_memo="P2P"
        ),
        Transaction(
            transaction_id="TX-SMURF-005",
            timestamp="2026-11-18T16:45:00Z",
            source_account="ACC-MULE-COLLECTOR",
            destination_account="ACC-EXIT-PORT",
            amount=380000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-3005",
            narrative_memo="OTC Escrow settlement"
        )
    ]


def get_case_planted_defects() -> List[Transaction]:
    """
    Scenario 4: Planted Defect Benchmark (RT-4088)
    Contains deliberately engineered defects:
    - Chronological violation: TX-DEFECT-002 occurs BEFORE TX-DEFECT-001 along flow
    - Non-positive / corrupted transaction amount in TX-DEFECT-003
    Used to verify that the Deterministic Stress Engine catches data anomalies.
    """
    return [
        Transaction(
            transaction_id="TX-DEFECT-001",
            timestamp="2026-11-22T10:00:00Z",
            source_account="ACC-CORRUPT-A",
            destination_account="ACC-CORRUPT-B",
            amount=150000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-4001",
            narrative_memo="Valid initiation"
        ),
        Transaction(
            transaction_id="TX-DEFECT-002",
            timestamp="2026-11-22T08:00:00Z",  # TIME TRAVEL: 2 hours BEFORE preceding transfer!
            source_account="ACC-CORRUPT-B",
            destination_account="ACC-CORRUPT-C",
            amount=145000.0,
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-4002",
            narrative_memo="Chronological impossibility",
            is_planted_defect=True,
            defect_description="Retrocausal timestamp: occurs before source funds arrived."
        ),
        Transaction(
            transaction_id="TX-DEFECT-003",
            timestamp="2026-11-22T12:00:00Z",
            source_account="ACC-CORRUPT-C",
            destination_account="ACC-CORRUPT-D",
            amount=-5000.0,  # INVALID AMOUNT: negative value
            currency="INR",
            transaction_type="transfer",
            source_record_id="SRC-REC-4003",
            narrative_memo="Invalid amount corruption",
            is_planted_defect=True,
            defect_description="Non-positive transaction amount."
        )
    ]


def get_all_preset_cases() -> Dict[str, Dict[str, Any]]:
    """Returns a lookup dictionary of all preset demonstration cases."""
    return {
        "RT-1042": {
            "case_id": "RT-1042",
            "title": "Circular Mule Ring (Rapid Pass-Through)",
            "description": "5-account layering cycle with high transit velocity and a pivotal bridge transaction.",
            "transactions": get_case_mule_ring()
        },
        "RT-2091": {
            "case_id": "RT-2091",
            "title": "Corporate Payroll Disbursement (False Positive Challenge)",
            "description": "High fan-out disbursement triggering anomaly flags, but explained by recurring salary structures.",
            "transactions": get_case_payroll_false_positive()
        },
        "RT-3015": {
            "case_id": "RT-3015",
            "title": "Smurfing Fan-In Aggregation",
            "description": "Multiple feeder accounts aggregating funds into a collection mule with rapid pass-through exit.",
            "transactions": get_case_smurf_aggregation()
        },
        "RT-4088": {
            "case_id": "RT-4088",
            "title": "Planted-Defect Data Integrity Benchmark",
            "description": "Contains deliberate retroactive timestamps, non-positive amounts, and unanchored citations.",
            "transactions": get_case_planted_defects()
        }
    }
