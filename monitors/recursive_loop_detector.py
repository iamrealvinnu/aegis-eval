import hashlib
import logging

logger = logging.getLogger("Aegis-Loop-Detector")

class LoopDetector:
    """
    This is my guard against the "Recursive Trap". 
    If the AI gets stuck in a loop of generating the same broken code, 
    this class will catch it and tell the orchestrator to pull the plug.
    """
    def __init__(self, threshold: int = 3):
        # I'm keeping a history of code hashes here.
        self.state_hashes = []
        # threshold is how many times we see the same code before we call it a loop.
        self.threshold = threshold  

    def hash_code(self, code: str) -> str:
        """
        I'm normalizing the code by stripping all whitespace before hashing.
        This prevents the AI from "tricking" the detector by just changing 
        indentation or adding spaces.
        """
        normalized = "".join(code.split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def is_looping(self, new_code: str) -> bool:
        """
        The main check. I hash the new code and see if it matches anything in our history.
        """
        current_hash = self.hash_code(new_code)
        
        # Checking how many times this exact code state has appeared.
        occurrences = self.state_hashes.count(current_hash)
        
        if occurrences >= self.threshold:
            # If we hit the limit, it's a critical safety event.
            logger.critical(f"Entropy-Driven Stream Interrupt Triggered: State {current_hash[:8]} repeated {occurrences} times.")
            return True
            
        # If it's new (or below threshold), we add it to history and keep going.
        self.state_hashes.append(current_hash)
        return False
