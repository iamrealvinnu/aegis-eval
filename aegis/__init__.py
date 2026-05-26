"""
Aegis-Eval: Autonomous AI Risk Assessment & Mitigation Framework
V2.0 - Advanced Threat Mitigation (Honeypots, Network Proxy, Swarm Security)
"""

from .core.orchestrator import SafetyOrchestrator
from .monitors.context_gatekeeper import ContextGatekeeper
from .monitors.exfiltration_detector import ExfiltrationDetector
from .monitors.intent_analyzer import IntentAnalyzer
from .monitors.inter_agent_firewall import InterAgentFirewall

__version__ = "3.0.0"

class CognitiveFirewall:
    """
    High-level API for easy integration into LangChain or CrewAI.
    """
    def __init__(self, model_path=None, dna_path="prompts/safety_dna.json"):
        self.orchestrator = SafetyOrchestrator(model_path=model_path)
        self.gatekeeper = ContextGatekeeper(dna_path=dna_path)
        
    async def verify_code(self, code, role="code_optimizer"):
        """
        Static verification of code before execution.
        """
        intent_report = self.orchestrator.intent_analyzer.analyze(code)
        strings = self.orchestrator.intent_analyzer.extract_strings(code)
        gatekeeper_report = self.gatekeeper.validate_access(role, strings)
        
        return {
            "intent": intent_report,
            "data_perimeter": gatekeeper_report
        }
