"""
RingTrace: Evidence Pack & Case Snapshot Generator
Creates an immutable, cryptographically hashed evidence pack containing verified records,
computed temporal paths, detected patterns, and explicit records of missing context.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
import hashlib
import json
from backend.models.schemas import Transaction, EvidencePack
from backend.graph.temporal_graph import TemporalTransactionGraph
from backend.graph.detectors import CandidatePatternDetector


def compute_evidence_hash(case_id: str, transactions: List[Transaction]) -> str:
    """Computes a SHA-256 hash over the sorted canonical transaction records."""
    canonical_repr = []
    for tx in sorted(transactions, key=lambda x: (x.timestamp, x.transaction_id)):
        canonical_repr.append(f"{tx.transaction_id}|{tx.timestamp}|{tx.source_account}|{tx.destination_account}|{tx.amount:.2f}|{tx.currency}")
    
    raw_payload = f"{case_id}::" + ";;".join(canonical_repr)
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


class EvidencePackBuilder:
    """Builds and freezes the immutable EvidencePack for an investigation case."""

    @staticmethod
    def build_evidence_pack(case_id: str, transactions: List[Transaction], dataset_version: str = "synthetic-v1.0") -> EvidencePack:
        # Build temporal graph
        graph = TemporalTransactionGraph(transactions)
        
        # Extract candidate patterns
        detector = CandidatePatternDetector(graph)
        patterns = detector.detect_all_patterns()
        
        # Discover time-respecting paths
        paths = graph.find_time_respecting_paths(max_hops=6, max_window_hours=72.0)
        
        # Extract accounts
        accounts = graph.get_account_nodes()
        
        # Calculate summary metrics
        total_volume = sum(t.amount for t in transactions)
        all_timestamps = [t.timestamp for t in transactions]
        min_time = min(all_timestamps) if all_timestamps else ""
        max_time = max(all_timestamps) if all_timestamps else ""

        metrics = {
            "total_transaction_count": len(transactions),
            "total_account_count": len(accounts),
            "total_volume": round(total_volume, 2),
            "currency": transactions[0].currency if transactions else "INR",
            "earliest_transaction": min_time,
            "latest_transaction": max_time,
            "pattern_count": len(patterns),
            "valid_path_count": len(paths)
        }

        # Explicitly catalog missing context / fields required for definitive intent determinations
        missing_fields = [
            "customer_declared_business_purpose",
            "source_of_funds_documentation",
            "external_tax_invoicing_records",
            "cross_institution_bank_silo_attributes",
            "beneficial_ownership_registry_match"
        ]

        provenance_hash = compute_evidence_hash(case_id, transactions)
        frozen_time = datetime.now(timezone.utc).isoformat()

        return EvidencePack(
            case_id=case_id,
            dataset_version=dataset_version,
            frozen_at=frozen_time,
            transactions=transactions,
            accounts=accounts,
            patterns=patterns,
            paths=paths,
            calculated_metrics=metrics,
            missing_fields=missing_fields,
            provenance_hash=provenance_hash
        )
