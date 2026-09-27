import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import pytest
from pydantic import BaseModel

from backend.app.models.simulator import DemoExecutionScope
from backend.app.analytics.unmet_demand_engine import UnmetDemandAssessmentEngine
from backend.app.analytics.convergence_engine import ConvergenceOpportunityEngine
from backend.app.analytics.priority_engine import ConvergencePriorityEngine
from backend.app.data.analytics_repository import AnalyticsRepository
from backend.app.data.demand_evidence_repository import CitizenDemandEvidenceRepository
from backend.app.data.unmet_demand_repository import UnmetDemandRepository
from backend.app.data.convergence_repository import ConvergenceOpportunityRepository
from backend.app.data.priority_assessment_repository import PriorityAssessmentRepository
from backend.app.models.demand_evidence import CitizenDemandEvidence
from backend.app.models.unmet_demand import UnmetDemandAssessment
from backend.app.models.convergence_opportunity import ConvergenceOpportunity
from backend.app.analytics.engine import PriorityWeights

def test_unmet_demand_targeted_scope():
    analytics_repo = MagicMock(spec=AnalyticsRepository)
    demand_repo = MagicMock(spec=CitizenDemandEvidenceRepository)
    unmet_repo = MagicMock(spec=UnmetDemandRepository)

    # Mock data with multiple villages
    class MockPublic(BaseModel):
        reported_household_gap: int = 100
        household_exposure: int = 1000

    analytics_repo._data = {
        "111111": MockPublic(),
        "222222": MockPublic()
    }

    now = datetime.now(timezone.utc)
    demand_repo.load_all.return_value = [
        CitizenDemandEvidence(
            demand_id="1", lgd_village_code="111111", canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER", signal_count=1, distinct_submitter_count=1,
            aggregation_window_start=now, aggregation_window_end=now, generated_at=now,
            source_channels=["mock"], latest_signal_at=now, contributing_signal_ids=["1"]
        ),
        CitizenDemandEvidence(
            demand_id="2", lgd_village_code="222222", canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER", signal_count=1, distinct_submitter_count=1,
            aggregation_window_start=now, aggregation_window_end=now, generated_at=now,
            source_channels=["mock"], latest_signal_at=now, contributing_signal_ids=["2"]
        )
    ]

    engine = UnmetDemandAssessmentEngine(analytics_repo, demand_repo, unmet_repo)

    # Run with scope
    scope = DemoExecutionScope(lgd_village_code="111111", canonical_need_type="WATER_SUPPLY_DEFICIT")
    assessments = engine.run_assessment(scope=scope)

    assert len(assessments) == 1
    assert assessments[0].lgd_village_code == "111111"
    assert assessments[0].canonical_need_type == "WATER_SUPPLY_DEFICIT"

    # Should call upsert, not overwrite
    unmet_repo.upsert_assessments.assert_called_once()
    unmet_repo.overwrite_assessments.assert_not_called()

def test_convergence_engine_targeted_scope():
    unmet_repo = MagicMock(spec=UnmetDemandRepository)
    conv_repo = MagicMock(spec=ConvergenceOpportunityRepository)

    now = datetime.now(timezone.utc)
    unmet_repo.load_all.return_value = [
        UnmetDemandAssessment(
            assessment_id="1", lgd_village_code="111111", canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER", evidence_state="DEMAND_SUPPORTED", assessment_date=now, assessment_version="v1"
        ),
        UnmetDemandAssessment(
            assessment_id="2", lgd_village_code="222222", canonical_need_type="WATER_SUPPLY_DEFICIT",
            sector="WATER", evidence_state="DEMAND_SUPPORTED", assessment_date=now, assessment_version="v1"
        )
    ]

    engine = ConvergenceOpportunityEngine(unmet_repo, conv_repo)
    scope = DemoExecutionScope(lgd_village_code="111111", canonical_need_type="WATER_SUPPLY_DEFICIT")
    opps = engine.evaluate_opportunities(scope=scope)

    assert len(opps) == 1
    assert opps[0].lgd_village_code == "111111"

    conv_repo.upsert_opportunities.assert_called_once()
    conv_repo.overwrite_opportunities.assert_not_called()

def test_priority_engine_targeted_scope():
    weights = PriorityWeights()
    conv_repo = MagicMock(spec=ConvergenceOpportunityRepository)
    prio_repo = MagicMock(spec=PriorityAssessmentRepository)

    now = datetime.now(timezone.utc)
    conv_repo.load_all.return_value = [
        ConvergenceOpportunity(
            opportunity_id="1", assessment_id="1", lgd_village_code="111111",
            canonical_need_type="WATER_SUPPLY_DEFICIT", sector="WATER", convergence_state="CONVERGENCE_IDENTIFIED",
            scheme_status="NOT_AVAILABLE", evaluated_at=now, calculation_version="v1"
        ),
        ConvergenceOpportunity(
            opportunity_id="2", assessment_id="2", lgd_village_code="222222",
            canonical_need_type="WATER_SUPPLY_DEFICIT", sector="WATER", convergence_state="CONVERGENCE_IDENTIFIED",
            scheme_status="NOT_AVAILABLE", evaluated_at=now, calculation_version="v1"
        )
    ]

    engine = ConvergencePriorityEngine(weights, conv_repo, prio_repo)
    scope = DemoExecutionScope(lgd_village_code="111111", canonical_need_type="WATER_SUPPLY_DEFICIT")
    prios = engine.calculate_priorities(scope=scope)

    assert len(prios) == 1
    assert prios[0].lgd_village_code == "111111"

    prio_repo.upsert_assessments.assert_called_once()
    prio_repo.overwrite_assessments.assert_not_called()
