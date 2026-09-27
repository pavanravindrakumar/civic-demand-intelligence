from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional
from backend.app.models.civic_need import NeedType, SectorType
from backend.app.models.evidence_ledger import EvidenceLedgerEntry
from backend.app.data.evidence_ledger_repository import evidence_ledger_repository

router = APIRouter(prefix="/api/evidence/ledger", tags=["Evidence Ledger"])

@router.get("", response_model=List[EvidenceLedgerEntry])
def get_ledger_entries(
    lgd_village_code: Optional[str] = Query(None, pattern=r"^\d{6}$"),
    canonical_need_type: Optional[NeedType] = None,
    sector: Optional[SectorType] = None,
    priority_version: Optional[str] = None,
    calculation_version: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """
    Retrieve read-only audit records from the Evidence Ledger.
    Results are deterministically ordered by generated_at (descending) and ledger_entry_id.
    """
    all_entries = evidence_ledger_repository.load_all()
    filtered = []

    for entry in all_entries:
        if lgd_village_code and entry.lgd_village_code != lgd_village_code:
            continue
        if canonical_need_type and entry.canonical_need_type != canonical_need_type:
            continue
        if sector and entry.sector != sector:
            continue
        if priority_version and entry.priority_version != priority_version:
            continue
        if calculation_version and entry.calculation_version != calculation_version:
            continue

        filtered.append(entry)

    # Deterministic ordering: generated_at desc, then ledger_entry_id
    filtered.sort(key=lambda x: (-x.generated_at.timestamp(), x.ledger_entry_id))

    return filtered[:limit]


@router.get("/{priority_assessment_id}", response_model=List[EvidenceLedgerEntry])
def get_ledger_entry_detail(
    priority_assessment_id: str = Path(..., pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
):
    """
    Retrieve read-only audit records for a specific Priority Assessment.
    Returns a list because a single assessment might hypothetically have been regenerated,
    though idempotency prevents identical duplicates.
    """
    entries = evidence_ledger_repository.get_by_priority_assessment_id(priority_assessment_id)

    if not entries:
        raise HTTPException(status_code=404, detail="Evidence ledger entry not found for assessment")

    entries.sort(key=lambda x: (-x.generated_at.timestamp(), x.ledger_entry_id))
    return entries
