import logging
import re

logger = logging.getLogger("Aegis-Swarm-Firewall")

class InterAgentFirewall:
    """
    This is the "Swarm Security" layer. 
    It mediates communication between agents to prevent sensitive data 
    leaking from one agent's context to another.
    """
    def __init__(self, global_secrets=None):
        self.global_secrets = global_secrets or []

    def sanitize_message(self, sender_role: str, receiver_role: str, message: str) -> str:
        """
        Redacts or blocks sensitive content in messages passed between agents.
        """
        logger.info(f"Filtering message from {sender_role} to {receiver_role}...")
        
        sanitized = message
        found_leaks = []

        # 1. Redact Global Secrets (Honeypots, etc.)
        for secret in self.global_secrets:
            if secret in message:
                found_leaks.append(f"Secret leakage detected: {secret[:4]}...")
                sanitized = sanitized.replace(secret, "[REDACTED_BY_AEGIS]")

        # 2. Heuristic PII Detection (Email, Phone, etc.)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, sanitized):
            logger.warning(f"PII Leakage Detected: Email pattern found.")
            sanitized = re.sub(email_pattern, "[REDACTED_PII]", sanitized)

        if found_leaks:
            logger.warning(f"Inter-Agent Firewall triggered: {len(found_leaks)} violations sanitized.")

        return sanitized

    def validate_flow(self, sender_role: str, receiver_role: str, payload: dict) -> bool:
        """
        Policy-based check: Is this specific role allowed to send this 
        type of payload to the receiver?
        """
        # For V2.0, we implement a simple rule: 
        # 'data_analyst' cannot send raw code to 'code_optimizer' if it's not verified.
        if sender_role == "data_analyst" and "code" in payload:
            logger.error(f"Unauthorized payload flow: {sender_role} tried to send code to {receiver_role}.")
            return False
            
        return True
