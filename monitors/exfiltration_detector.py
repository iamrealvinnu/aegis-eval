import math
import logging

logger = logging.getLogger("Aegis-Exfiltration")

class ExfiltrationDetector:
    """
    This is the "Entropy Monitor". I'm looking for "Drip-Fed Leakage".
    If an AI reads a lot of data and outputs a tiny, dense string, 
    it might be exfiltrating a secret key.
    """
    def __init__(self, entropy_threshold: float = 4.5):
        # A threshold of ~4.5 is usually where random-looking keys and 
        # base64 secrets start to appear.
        self.entropy_threshold = entropy_threshold

    def _calculate_entropy(self, text: str) -> float:
        """
        Standard Shannon Entropy calculation. 
        High entropy = Randomness (Key-like data).
        Low entropy = Natural language.
        """
        if not text:
            return 0.0
        
        probs = [text.count(c) / len(text) for c in set(text)]
        entropy = -sum(p * math.log2(p) for p in probs)
        return entropy

    def analyze_output(self, output: str) -> dict:
        """
        I scan the agent's output for suspicious data-flow patterns.
        """
        entropy = self._calculate_entropy(output)
        
        # If the output is small but has massive entropy, it's a huge red flag.
        if len(output) > 20 and entropy > self.entropy_threshold:
            logger.critical(f"Exfiltration Alert: High-entropy output detected ({entropy:.2f}). Possible secret leakage.")
            return {
                "status": "warning", 
                "reason": "High-entropy output (potential secret key/base64 leak)",
                "entropy": entropy
            }
            
        return {"status": "safe", "entropy": entropy}
