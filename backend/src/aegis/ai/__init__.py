"""AI layer: fail-safe parsing of structured output + post-AI numeric reconciliation.

The AI decides/explains; Python owns every number (C-2). This package never lets an invalid
or hallucinated AI output reach the operator (C-4/AC-04/AC-05).
"""

from aegis.ai.failsafe import AISignalDecision, parse_ai_decision, should_emit
from aegis.ai.orchestrator import AIClient, ModelRouting, SignalOrchestrator
from aegis.ai.reconciliation import (
    ReconciliationResult,
    build_signal_from_decision,
    reconcile_signal,
)

__all__ = [
    "AIClient",
    "AISignalDecision",
    "ModelRouting",
    "ReconciliationResult",
    "SignalOrchestrator",
    "build_signal_from_decision",
    "parse_ai_decision",
    "reconcile_signal",
    "should_emit",
]
