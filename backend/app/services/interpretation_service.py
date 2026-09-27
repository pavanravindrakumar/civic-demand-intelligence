import logging
from typing import Optional, Tuple
from backend.app.models.signal import StoredCitizenSignal
from backend.app.models.civic_need import CivicNeed
from backend.app.analytics.interpreter import SignalInterpreter, InterpretationError
from backend.app.data.civic_need_repository import CivicNeedRepository

logger = logging.getLogger(__name__)

class CivicNeedInterpretationService:
    def __init__(
        self,
        interpreter: SignalInterpreter,
        repository: CivicNeedRepository
    ):
        self.interpreter = interpreter
        self.repository = repository

    def interpret_signal(self, signal: StoredCitizenSignal) -> Tuple[bool, Optional[CivicNeed], str]:
        """
        Attempts to interpret a StoredCitizenSignal into a canonical CivicNeed.

        Returns:
            (success: bool, civic_need: Optional[CivicNeed], new_extraction_status: str)

        Updates the signal extraction_status based on the outcome, but does NOT persist
        the signal itself (that is the caller's responsibility or handled elsewhere if needed).
        If successful, persists the CivicNeed via the injected repository.
        """
        # 1. Idempotency Check
        existing_need = self.repository.get_by_source_signal_id(signal.signal_id)
        if existing_need:
            logger.info(f"Signal {signal.signal_id} already interpreted. Returning existing record.")
            signal.extraction_status = "INTERPRETED"
            return True, existing_need, signal.extraction_status

        # 2. Invoke Interpreter
        try:
            civic_need = self.interpreter.interpret(signal)

            # The interpreter constructs the CivicNeed and its metadata.
            # We strictly enforce that provenance is preserved here in the service layer
            # just in case the interpreter missed it, though our design puts building in the interpreter.
            if civic_need.source_signal_id != signal.signal_id:
                raise ValueError("Interpreter returned mismatched source_signal_id")

            # 3. Persist Validated Result
            stored_need = self.repository.store_civic_need(civic_need)
            signal.extraction_status = "INTERPRETED"

            return True, stored_need, signal.extraction_status

        except InterpretationError as e:
            logger.warning(f"Interpretation refused for signal {signal.signal_id}: {e}")
            signal.extraction_status = "FAILED"
            return False, None, signal.extraction_status

        except Exception as e:
            logger.error(f"Unexpected error interpreting signal {signal.signal_id}: {e}")
            signal.extraction_status = "FAILED"
            return False, None, signal.extraction_status
