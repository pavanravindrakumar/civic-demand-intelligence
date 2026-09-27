from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone, timedelta
import uuid
import os
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

from backend.app.models.simulator import ScenarioType
from backend.app.copilot.gemini_client import get_client, GeminiConfig, GeminiProviderMode
from backend.app.orchestrator.synthetic_pipeline import SyntheticCivicIntelligenceOrchestrator, SyntheticPipelineSummary
from backend.app.api.middleware import demo_limiter

# Repositories
from backend.app.data.synthetic_signal_repository import synthetic_signal_repository
from backend.app.data.analytics_repository import AnalyticsRepository
from backend.app.data.civic_need_repository import civic_need_repository
from backend.app.data.demand_evidence_repository import demand_evidence_repository
from backend.app.data.unmet_demand_repository import unmet_demand_repository
from backend.app.data.convergence_repository import convergence_repository
from backend.app.data.priority_assessment_repository import priority_assessment_repository
from backend.app.data.evidence_ledger_repository import evidence_ledger_repository

analytics_repository = AnalyticsRepository()

# Services & Engines
from backend.app.services.simulator_service import CivicSignalSimulator
from backend.app.services.interpretation_service import CivicNeedInterpretationService
from backend.app.analytics.interpreter import SignalInterpreter, GeminiInterpreter
from backend.app.models.civic_need import CivicNeed
from backend.app.analytics.demand_aggregator import CitizenDemandAggregator
from backend.app.analytics.unmet_demand_engine import UnmetDemandAssessmentEngine
from backend.app.analytics.convergence_engine import ConvergenceOpportunityEngine
from backend.app.analytics.priority_engine import ConvergencePriorityEngine, PriorityWeights
from backend.app.analytics.evidence_ledger_service import EvidenceLedgerService

router = APIRouter(prefix="/api/demo/scenarios", tags=["demo"])

class DemoScenarioRunRequest(BaseModel):
    scenario_id: ScenarioType
    simulation_version: str = Field(default="demo-v1.0")
    seed: str = Field(default="demo-seed-default")
    batch_size: int = Field(default=5, ge=1, le=50)

class DemoScenarioRunResponse(BaseModel):
    scenario_id: str
    simulation_version: str
    pipeline_status: str
    ai_interpretation_mode: str = "DEMO / DETERMINISTIC MOCK"

    lgd_village_code: Optional[str] = None

    generated_signal_count: int = 0
    interpreted_need_count: int = 0
    demand_evidence_count: int = 0
    unmet_demand_assessment_count: int = 0
    convergence_opportunity_count: int = 0
    priority_assessment_count: int = 0
    evidence_ledger_count: int = 0

    citizen_evidence_provenance: str = "SYNTHETIC_DEMO_SIGNAL"
    public_evidence_provenance: str = "REAL_JJM_LGD"

    error_stage: Optional[str] = None
    error_code: Optional[str] = None

class DemoMockInterpreter(SignalInterpreter):
    """
    Offline mock interpreter explicitly avoiding live Gemini calls for the Demo API.
    """
    def interpret(self, signal) -> CivicNeed:
        if "road" in signal.raw_text.lower() or "రోడ్డు" in signal.raw_text.lower() or "sadak" in signal.raw_text.lower():
            need = "ROAD_CONNECTIVITY_DEFICIT"
            sector = "ROADS"
        else:
            need = "WATER_SUPPLY_DEFICIT"
            sector = "WATER"

        return CivicNeed(
            need_id=f"need_{signal.signal_id}",
            source_signal_id=signal.signal_id,
            canonical_need_type=need,
            sector=sector,
            lgd_village_code=signal.lgd_village_code,
            detected_language=signal.detected_language,
            first_seen_at=signal.submitted_at,
            source_channel=signal.source,
            processing_version="mock-v1.0",
            need_label_en="Mock Interpreted Need",
            location_expression="Mock Location",
            location_confidence=0.9,
            urgency="MEDIUM",
            last_updated_at=signal.submitted_at
        )

# Dependency to inject Orchestrator
def get_demo_orchestrator() -> SyntheticCivicIntelligenceOrchestrator:
    simulator = CivicSignalSimulator(synthetic_signal_repository, analytics_repository)

    interpreter = DemoMockInterpreter()
    interp_service = CivicNeedInterpretationService(interpreter, civic_need_repository)

    aggregator = CitizenDemandAggregator(demand_evidence_repository)
    unmet_engine = UnmetDemandAssessmentEngine(analytics_repository, demand_evidence_repository, unmet_demand_repository)
    conv_engine = ConvergenceOpportunityEngine(unmet_demand_repository, convergence_repository)

    weights = PriorityWeights()
    prio_engine = ConvergencePriorityEngine(weights, convergence_repository, priority_assessment_repository)

    ledger_service = EvidenceLedgerService(evidence_ledger_repository)

    return SyntheticCivicIntelligenceOrchestrator(
        simulator, interp_service, aggregator, unmet_engine, conv_engine, prio_engine, ledger_service
    )

@router.post("/run", response_model=DemoScenarioRunResponse)
def run_demo_scenario(request: DemoScenarioRunRequest, orchestrator: SyntheticCivicIntelligenceOrchestrator = Depends(get_demo_orchestrator)):
    """
    Run a controlled Synthetic Civic Intelligence Demo scenario offline.
    """
    now = datetime.now(timezone.utc)
    # Controlled window matching standard demo constraints
    window_start = now - timedelta(days=30)
    window_end = now + timedelta(days=30)

    summary = orchestrator.run_pipeline(
        scenario_id=request.scenario_id,
        version=request.simulation_version,
        window_start=window_start,
        window_end=window_end,
        seed=request.seed,
        batch_size=request.batch_size
    )

    # Map the summary to our typed Demo response
    response = DemoScenarioRunResponse(
        scenario_id=summary.scenario_id,
        simulation_version=summary.simulation_version,
        pipeline_status=summary.pipeline_status,
        lgd_village_code=summary.targeted_lgd_village_code,
        generated_signal_count=summary.generated_signal_count,
        interpreted_need_count=summary.interpreted_need_count,
        demand_evidence_count=summary.demand_evidence_count,
        unmet_demand_assessment_count=summary.unmet_demand_assessment_count,
        convergence_opportunity_count=summary.convergence_opportunity_count,
        priority_assessment_count=summary.priority_assessment_count,
        evidence_ledger_count=summary.ledger_entry_count,
        citizen_evidence_provenance=summary.citizen_evidence_provenance,
        public_evidence_provenance=summary.public_evidence_provenance,
    )

    if summary.pipeline_status == "FAILED":
        response.error_stage = summary.error_stage
        response.error_code = "PIPELINE_ERROR"
        raise HTTPException(status_code=500, detail={"status": "FAILED", "stage": summary.error_stage})

    return response

class LiveDemoResponse(DemoScenarioRunResponse):
    gemini_request_count: int = 0
    gemini_model: Optional[str] = None
    canonical_need_type: Optional[str] = None
    detected_language: Optional[str] = None

def get_live_demo_orchestrator() -> SyntheticCivicIntelligenceOrchestrator:
    # Check Feature Flag
    if os.environ.get("DEMO_LIVE_GEMINI_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="LIVE_GEMINI_DEMO_DISABLED")

    # Get Gemini Client
    try:
        model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
        config = GeminiConfig(
            gemini_model=model,
            provider_mode=GeminiProviderMode.DEVELOPER_API,
            api_key=os.environ.get("GEMINI_API_KEY")
        )
        client = get_client(config)
    except Exception as e:
        logger.error("Gemini Configuration Failure", extra={"safe_context": {"error_type": type(e).__name__, "operation": "live_demo"}})
        raise HTTPException(status_code=500, detail="Gemini Configuration Failure")

    simulator = CivicSignalSimulator(synthetic_signal_repository, analytics_repository)

    interpreter = GeminiInterpreter(client=client, gemini_model=model)
    interp_service = CivicNeedInterpretationService(interpreter, civic_need_repository)

    aggregator = CitizenDemandAggregator(demand_evidence_repository)
    unmet_engine = UnmetDemandAssessmentEngine(analytics_repository, demand_evidence_repository, unmet_demand_repository)
    conv_engine = ConvergenceOpportunityEngine(unmet_demand_repository, convergence_repository)

    weights = PriorityWeights()
    prio_engine = ConvergencePriorityEngine(weights, convergence_repository, priority_assessment_repository)

    ledger_service = EvidenceLedgerService(evidence_ledger_repository)

    return SyntheticCivicIntelligenceOrchestrator(
        simulator, interp_service, aggregator, unmet_engine, conv_engine, prio_engine, ledger_service
    )

@router.post("/live/water-convergence", response_model=LiveDemoResponse, dependencies=[Depends(demo_limiter)])
def run_live_water_convergence(orchestrator: SyntheticCivicIntelligenceOrchestrator = Depends(get_live_demo_orchestrator)):
    """
    Controlled Live-AI Demo endpoint for the Hackathon.
    Executes exactly one Gemini request for the WATER_CONVERGENCE scenario.
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=30)
    window_end = now + timedelta(days=30)

    try:
        # Strictly batch_size=1 and scenario_id="WATER_CONVERGENCE"
        summary = orchestrator.run_pipeline(
            scenario_id="WATER_CONVERGENCE",
            version="live-demo-v1.0",
            window_start=window_start,
            window_end=window_end,
            seed=f"live-demo-seed-{uuid.uuid4()}",
            batch_size=1,
            targeted_execution=True
        )
    except Exception as e:
        logger.error("Live Demo Orchestrator Failure", extra={"safe_context": {"error_type": type(e).__name__, "operation": "live_demo"}})
        # Avoid leaking exceptions
        return LiveDemoResponse(
            scenario_id="WATER_CONVERGENCE",
            simulation_version="live-demo-v1.0",
            pipeline_status="FAILED",
            error_stage="ORCHESTRATOR",
            error_code="UNEXPECTED_FAILURE",
            ai_interpretation_mode="LIVE GEMINI DEMONSTRATION"
        )

    if summary.pipeline_status == "COMPLETED" and summary.interpreted_need_count == 0 and summary.generated_signal_count > 0:
        summary.pipeline_status = "FAILED"
        summary.error_stage = "INTERPRETATION"

    response = LiveDemoResponse(
        scenario_id=summary.scenario_id,
        simulation_version=summary.simulation_version,
        pipeline_status=summary.pipeline_status,
        ai_interpretation_mode="LIVE GEMINI DEMONSTRATION",
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),

        # We manually count 1 gemini request if we reached here with interpreted needs
        gemini_request_count=1 if summary.interpreted_need_count > 0 else 0,

        generated_signal_count=summary.generated_signal_count,
        interpreted_need_count=summary.interpreted_need_count,
        demand_evidence_count=summary.demand_evidence_count,
        unmet_demand_assessment_count=summary.unmet_demand_assessment_count,
        convergence_opportunity_count=summary.convergence_opportunity_count,
        priority_assessment_count=summary.priority_assessment_count,
        evidence_ledger_count=summary.ledger_entry_count,
        citizen_evidence_provenance=summary.citizen_evidence_provenance,
        public_evidence_provenance=summary.public_evidence_provenance,
        lgd_village_code=summary.targeted_lgd_village_code if hasattr(summary, 'targeted_lgd_village_code') else None,
    )

    if summary.pipeline_status == "FAILED":
        response.error_stage = summary.error_stage
        response.error_code = "PIPELINE_ERROR"
        # Return success with a failed status, rather than HTTP 500, to prevent raw traceback leaks
        return response

    return response
