import os
import json
import logging
from unittest.mock import patch
from dotenv import load_dotenv

# Ensure DEMO is enabled for the smoke test
os.environ["DEMO_LIVE_GEMINI_ENABLED"] = "true"

from fastapi.testclient import TestClient
from backend.app.main import app

from backend.app.data.civic_need_repository import civic_need_repository
from backend.app.data.demand_evidence_repository import demand_evidence_repository
from backend.app.data.unmet_demand_repository import unmet_demand_repository
from backend.app.data.convergence_repository import convergence_repository
from backend.app.data.priority_assessment_repository import priority_assessment_repository
from backend.app.data.evidence_ledger_repository import evidence_ledger_repository
from backend.app.data.synthetic_signal_repository import synthetic_signal_repository

from backend.app.api.demo_api import get_client as original_get_client

gemini_call_count = 0

def wrapped_get_client(config):
    client = original_get_client(config)
    original_generate = client.models.generate_content

    def wrapped_generate(*args, **kwargs):
        global gemini_call_count
        gemini_call_count += 1
        return original_generate(*args, **kwargs)

    client.models.generate_content = wrapped_generate
    return client

def clean_temporary_artifacts():
    paths = [
        "data/local_development/synthetic_citizen_signals.jsonl",
        "data/local_development/civic_needs.jsonl",
        "data/local_development/citizen_demand_evidence.jsonl",
        "data/local_development/unmet_demand_assessments.jsonl",
        "data/local_development/convergence_opportunities.jsonl",
        "data/local_development/priority_assessments.jsonl",
        "data/local_development/evidence_ledger.jsonl"
    ]
    for path in paths:
        if os.path.exists(path):
            os.remove(path)

if __name__ == "__main__":
    load_dotenv()
    # Explicitly set enabled flag for test
    os.environ["DEMO_LIVE_GEMINI_ENABLED"] = "true"

    print("Cleaning temp artifacts before run...")
    clean_temporary_artifacts()

    from backend.app.api.demo_api import run_live_water_convergence, get_live_demo_orchestrator

    print("Executing Phase 9.1B Live Smoke Test...")
    try:
        with patch("backend.app.api.demo_api.get_client", side_effect=wrapped_get_client):
            orchestrator = get_live_demo_orchestrator()
            response = run_live_water_convergence(orchestrator)

            # response is a Pydantic model
            data = response.model_dump()
            print("\n================== API RESPONSE ==================")
            print(json.dumps(data, indent=2))

            print(f"\nInstrumented Gemini SDK Call Count: {gemini_call_count}")

            # Load from repositories to inspect
            signals = synthetic_signal_repository.load_all()
            demands = demand_evidence_repository.load_all()
            unmets = unmet_demand_repository.load_all()
            opportunities = convergence_repository.load_all()
            priorities = priority_assessment_repository.load_all()
            ledgers = evidence_ledger_repository.load_all()

            print("\n================== DOWNSTREAM PIPELINE ==================")

            print(f"Synthetic Signals Generated: {len(signals)}")
            if signals:
                sig = signals[0]
                print(f"  Signal Language: {sig.detected_language}")
                print(f"  Signal Village: {sig.lgd_village_code}")
                print(f"  Signal Provenance: {sig.provenance}")

                need = civic_need_repository.get_by_source_signal_id(sig.signal_id)
                if need:
                    print(f"\nCivic Needs Extracted: 1")
                    print(f"  Canonical Need: {need.canonical_need_type}")
                    print(f"  Sector: {need.sector}")

                village_code = sig.lgd_village_code
                if village_code:
                    v_demands = [d for d in demands if d.lgd_village_code == village_code]
                    print(f"\nDemand Evidence for Village: {len(v_demands)}")

                    v_unmets = [u for u in unmets if u.lgd_village_code == village_code and u.canonical_need_type == "WATER_SUPPLY_DEFICIT"]
                    print(f"\nUnmet Demand for Village: {len(v_unmets)}")
                    if v_unmets:
                        print(f"  State: {v_unmets[0].evidence_state}")

                    v_opps = [o for o in opportunities if o.lgd_village_code == village_code and o.canonical_need_type == "WATER_SUPPLY_DEFICIT"]
                    print(f"\nConvergence Opportunity for Village: {len(v_opps)}")
                    if v_opps:
                        print(f"  State: {v_opps[0].convergence_state}")

                    v_prios = [p for p in priorities if p.lgd_village_code == village_code and p.canonical_need_type == "WATER_SUPPLY_DEFICIT"]
                    print(f"\nPriority Assessment for Village: {len(v_prios)}")
                    if v_prios:
                        print(f"  Score: {v_prios[0].priority_score}")
                        print(f"  Version: {v_prios[0].priority_version}")
                        print(f"  Factor Inputs: {v_prios[0].factor_inputs_normalized}")
                        print(f"  Factor Contributions: {v_prios[0].factor_contributions}")

                    v_ledgers = [l for l in ledgers if l.lgd_village_code == village_code]
                    print(f"\nEvidence Ledger Entries for Village: {len(v_ledgers)}")

    finally:
        print("\nCleaning temporary artifacts...")
        clean_temporary_artifacts()
        print("Done.")
