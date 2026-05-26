import logging
import fnmatch
import os
import json

logger = logging.getLogger("Aegis-Gatekeeper")

class ContextGatekeeper:
    """
    This is the "Data Perimeter". I'm sitting between the AI's intent 
    and the host's data. If the AI even mentions a forbidden file, 
    I'm blocking it before it touches the sandbox.
    """
    def __init__(self, dna_path: str = "prompts/safety_dna.json"):
        self.policy = {}
        if os.path.exists(dna_path):
            try:
                with open(dna_path, 'r') as f:
                    self.policy = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load Safety DNA: {e}")

    def validate_access(self, role: str, accessed_resources: list) -> dict:
        """
        I cross-reference every resource the AI mentioned against its 
        assigned role in the Safety DNA.
        """
        role_config = self.policy.get("roles", {}).get(role)
        if not role_config:
            # If we don't know the role, we fail-safe: DENY EVERYTHING.
            return {"status": "violation", "reason": f"Unknown role: {role}"}

        deny_patterns = role_config.get("deny", []) + self.policy.get("global_denylist", [])
        allow_patterns = role_config.get("allow", [])
        
        violations = []

        for resource in accessed_resources:
            # 1. Check Global and Role-Specific Denylist (The Hard No)
            for pattern in deny_patterns:
                if fnmatch.fnmatch(resource, pattern) or pattern in resource:
                    violations.append(f"Policy Violation: '{resource}' is explicitly DENIED for role '{role}'.")

            # 2. Check Allowlists (If not explicitly allowed, it might be risky)
            # This is optional based on how strict you want to be. 
            # For now, I'm focusing on the hard Denylist.

        if violations:
            return {"status": "violation", "violations": violations}
        
        return {"status": "safe"}
