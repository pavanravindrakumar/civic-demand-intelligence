from typing import List, Dict, Tuple, Set, Optional
import uuid
from datetime import datetime, timezone

from backend.app.models.civic_need import CivicNeed
from backend.app.models.demand_evidence import CitizenDemandEvidence
from backend.app.data.demand_evidence_repository import CitizenDemandEvidenceRepository

class CitizenDemandAggregator:
    def __init__(self, repository: CitizenDemandEvidenceRepository):
        self.repository = repository

    def aggregate_evidence(
        self,
        civic_needs: List[CivicNeed],
        window_start: datetime,
        window_end: datetime
    ) -> List[CitizenDemandEvidence]:
        """
        Aggregates validated CivicNeeds into deterministic CitizenDemandEvidence.
        Same CivicNeed inputs + same bounds -> exactly same demand evidence outputs.
        """

        # Grouping key: (canonical_need_type, lgd_village_code)
        # Value: list of contributing unique CivicNeeds
        groups: Dict[Tuple[str, Optional[str]], List[CivicNeed]] = {}

        # We must deduplicate by source_signal_id globally in the aggregate run.
        # If the same source_signal_id appears multiple times for the same need type/village,
        # it counts exactly once.
        seen_signals: Set[str] = set()

        for need in civic_need_records_in_window(civic_needs, window_start, window_end):
            # deduplicate by source signal ID per exact need type/geography combination
            # Actually, idempotency is global per signal, but here we enforce it strictly
            if need.source_signal_id in seen_signals:
                continue
            seen_signals.add(need.source_signal_id)

            key = (need.canonical_need_type, need.lgd_village_code)
            if key not in groups:
                groups[key] = []
            groups[key].append(need)

        aggregates: List[CitizenDemandEvidence] = []

        for (need_type, lgd_code), group_needs in groups.items():
            # Derived fields
            signal_count = len(group_needs)
            contributing_signal_ids = [n.source_signal_id for n in group_needs]
            latest_signal_at = max(n.first_seen_at for n in group_needs)
            sector = group_needs[0].sector

            channels = set(n.source_channel for n in group_needs)
            pseudonyms = set(n.submitter_pseudonym for n in group_needs if n.submitter_pseudonym)
            distinct_submitter_count = len(pseudonyms)

            agg = CitizenDemandEvidence(
                demand_id=str(uuid.uuid4()),
                canonical_need_type=need_type,
                sector=sector,
                lgd_village_code=lgd_code,
                aggregation_window_start=window_start,
                aggregation_window_end=window_end,
                signal_count=signal_count,
                distinct_submitter_count=distinct_submitter_count,
                source_channels=sorted(list(channels)),
                latest_signal_at=latest_signal_at,
                contributing_signal_ids=contributing_signal_ids,
                aggregation_version="demand-v1"
            )
            aggregates.append(agg)

        # Rebuild/overwrite the local derived artifact
        self.repository.overwrite_evidence(aggregates)
        return aggregates

def civic_need_records_in_window(needs: List[CivicNeed], start: datetime, end: datetime) -> List[CivicNeed]:
    return [n for n in needs if start <= n.first_seen_at <= end]
