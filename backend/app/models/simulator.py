from pydantic import BaseModel, Field
from typing import Literal, Optional, List

ScenarioType = Literal[
    "WATER_CONVERGENCE",
    "WATER_NO_PUBLIC_GAP",
    "NON_WATER_DEMAND",
    "UNRESOLVED_GEOGRAPHY"
]

class DemoExecutionScope(BaseModel):
    lgd_village_code: str
    canonical_need_type: str

class CivicSignalSimulationScenario(BaseModel):
    scenario_id: ScenarioType
    simulation_version: str
    target_lgd_village_code: Optional[str] = None
    batch_size: int = Field(default=10, ge=1, le=50)

class CivicSignalSimulationResult(BaseModel):
    scenario_id: ScenarioType
    simulation_version: str
    target_lgd_village_code: Optional[str] = None
    generated_count: int
    provenance: str = "SYNTHETIC_DEMO_SIGNAL"
