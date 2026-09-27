from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.app.models.simulator import ScenarioType, DemoExecutionScope
from backend.app.services.simulator_service import CivicSignalSimulator
from backend.app.services.interpretation_service import CivicNeedInterpretationService
from backend.app.analytics.demand_aggregator import CitizenDemandAggregator
from backend.app.analytics.unmet_demand_engine import UnmetDemandAssessmentEngine
from backend.app.analytics.convergence_engine import ConvergenceOpportunityEngine
from backend.app.analytics.priority_engine import ConvergencePriorityEngine
from backend.app.analytics.evidence_ledger_service import EvidenceLedgerService
from backend.app.models.signal import StoredCitizenSignal

class SyntheticPipelineSummary(BaseModel):
    scenario_id: str
    simulation_version: str
    pipeline_status: str
    error_stage: Optional[str] = None

    generated_signal_count: int = 0
    interpreted_need_count: int = 0
    demand_evidence_count: int = 0
    unmet_demand_assessment_count: int = 0
    convergence_opportunity_count: int = 0
    priority_assessment_count: int = 0
    ledger_entry_count: int = 0

    public_evidence_provenance: str = "REAL_JJM_LGD"
    citizen_evidence_provenance: str = "SYNTHETIC_DEMO_SIGNAL"
    targeted_lgd_village_code: Optional[str] = None

class SyntheticCivicIntelligenceOrchestrator:
    """
    Orchestrates the entire Civic Intelligence pipeline for synthetic scenarios.
    Pure orchestration: no business logic or math calculations are performed here.
    """
    def __init__(
        self,
        simulator: CivicSignalSimulator,
        interpretation_service: CivicNeedInterpretationService,
        demand_aggregator: CitizenDemandAggregator,
        unmet_demand_engine: UnmetDemandAssessmentEngine,
        convergence_engine: ConvergenceOpportunityEngine,
        priority_engine: ConvergencePriorityEngine,
        ledger_service: EvidenceLedgerService
    ):
        self.simulator = simulator
        self.interpretation_service = interpretation_service
        self.demand_aggregator = demand_aggregator
        self.unmet_demand_engine = unmet_demand_engine
        self.convergence_engine = convergence_engine
        self.priority_engine = priority_engine
        self.ledger_service = ledger_service

    def run_pipeline(
        self,
        scenario_id: ScenarioType,
        version: str,
        window_start: datetime,
        window_end: datetime,
        seed: str = "default",
        batch_size: int = 5,
        targeted_execution: bool = False
    ) -> SyntheticPipelineSummary:
        summary = SyntheticPipelineSummary(
            scenario_id=scenario_id,
            simulation_version=version,
            pipeline_status="STARTED"
        )

        try:
            # 1. Simulate Signals
            sim_res = self.simulator.generate_scenario(scenario_id, version, seed, batch_size=batch_size)
            summary.generated_signal_count = sim_res.generated_count
            summary.targeted_lgd_village_code = sim_res.target_lgd_village_code

            # Fetch the generated signals from the repository
            # Simple assumption: we just take the newly generated ones by this simulation run
            all_synthetic_signals = self.simulator.synthetic_repo._data if hasattr(self.simulator.synthetic_repo, "_data") else self.simulator.synthetic_repo.load_all() if hasattr(self.simulator.synthetic_repo, "load_all") else []
            # We filter by scenario and version to just run what we need
            batch_signals = [s for s in all_synthetic_signals if s.synthetic_scenario_id == scenario_id and s.processing_version == version]

            if not batch_signals:
                summary.pipeline_status = "COMPLETED"
                return summary

            # 2. Interpretation
            needs = []
            for sig in batch_signals:
                success, civic_need, status = self.interpretation_service.interpret_signal(sig)
                if success and civic_need:
                    needs.append(civic_need)

            summary.interpreted_need_count = len(needs)
            if not needs:
                summary.pipeline_status = "COMPLETED"
                return summary

            # 3. Demand Aggregation
            demands = self.demand_aggregator.aggregate_evidence(needs, window_start, window_end)
            summary.demand_evidence_count = len(demands)
            if not demands:
                summary.pipeline_status = "COMPLETED"
                return summary

            # Determine execution scope if targeted
            scope = None
            if targeted_execution and demands:
                scope = DemoExecutionScope(
                    lgd_village_code=demands[0].lgd_village_code,
                    canonical_need_type=demands[0].canonical_need_type
                )

            # 4. Unmet Demand Assessment
            unmet_assessments = self.unmet_demand_engine.run_assessment(scope=scope)
            # Only count the ones associated with our demands
            # Since the pipeline rebuilds all derived artifacts based on repos, we just count all that match our window/LGD
            # For a pure summary, let's just count total UnmetDemandAssessments produced that have demand
            if scope:
                demand_supported_unmets = [u for u in unmet_assessments if u.evidence_state == "DEMAND_SUPPORTED" and u.lgd_village_code == scope.lgd_village_code]
            else:
                demand_supported_unmets = [u for u in unmet_assessments if u.evidence_state == "DEMAND_SUPPORTED"]
            summary.unmet_demand_assessment_count = len(demand_supported_unmets)

            # 5. Convergence Opportunity
            opportunities = self.convergence_engine.evaluate_opportunities(scope=scope)
            if scope:
                convergence_identified = [o for o in opportunities if o.convergence_state == "CONVERGENCE_IDENTIFIED" and o.lgd_village_code == scope.lgd_village_code]
            else:
                convergence_identified = [o for o in opportunities if o.convergence_state == "CONVERGENCE_IDENTIFIED"]
            summary.convergence_opportunity_count = len(convergence_identified)

            # 6. Priority Engine
            priorities = self.priority_engine.calculate_priorities(scope=scope)
            if scope:
                scored_priorities = [p for p in priorities if p.priority_score is not None and p.lgd_village_code == scope.lgd_village_code]
            else:
                scored_priorities = [p for p in priorities if p.priority_score is not None]
            summary.priority_assessment_count = len(scored_priorities)

            # 7. Evidence Ledger
            # The ledger service acts on pairs of (PriorityAssessment, ConvergenceOpportunity)
            # The priority engine doesn't inherently call the ledger service in its bulk method
            # So the orchestrator wires them up for the ones produced
            # O(1) lookup map for opportunities
            opp_map = {o.opportunity_id: o for o in opportunities}

            ledger_count = 0
            for prio in priorities:
                # If targeted execution, only record the targeted priority
                if scope and (prio.lgd_village_code != scope.lgd_village_code or prio.canonical_need_type != scope.canonical_need_type):
                    continue

                # Find matching opportunity
                opp = opp_map.get(prio.opportunity_id)
                if opp:
                    self.ledger_service.record_assessment(prio, opp)
                    ledger_count += 1

            summary.ledger_entry_count = ledger_count
            summary.pipeline_status = "COMPLETED"

        except Exception as e:
            summary.pipeline_status = "FAILED"
            summary.error_stage = str(e)

        return summary
