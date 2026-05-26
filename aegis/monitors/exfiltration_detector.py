import math
import logging

logger = logging.getLogger("Aegis-Exfiltration")

class ExfiltrationDetector:
    """
    V3.0 Hardened Exfiltration Detector.
    Now tracks cumulative entropy across a session to detect drip-fed leaks.
    """
    def __init__(self, entropy_threshold: float = 4.5):
        self.entropy_threshold = entropy_threshold
        self.session_history = "" # Cumulative output for the session

    def _calculate_entropy(self, text: str) -> float:
        if not text: return 0.0
        probs = [text.count(c) / len(text) for c in set(text)]
        return -sum(p * math.log2(p) for p in probs)

    def check_honeypot_leak(self, output: str, honeypot_dna: dict) -> list:
        leaks = []
        for resource, content in honeypot_dna.items():
            for line in content.split('\n'):
                if '=' in line:
                    secret = line.split('=')[-1].strip()
                    if secret and secret in output:
                        leaks.append(f"Honeypot Leak: '{secret}' from '{resource}'")
                elif ':' in line:
                    import re
                    matches = re.findall(r'"[^"]+":\s*"([^"]+)"', line)
                    for secret in matches:
                        if secret and secret in output:
                            leaks.append(f"Honeypot Leak: '{secret}' from '{resource}'")
        return leaks

    def analyze_output(self, output: str) -> dict:
        """
        Hardened turn-by-turn analysis + Cumulative analysis.
        """
        # 1. Turn Entropy
        turn_entropy = self._calculate_entropy(output)
        
        # 2. Cumulative Session Entropy (Detecting 'Drip-Feed')
        self.session_history += output
        cumulative_entropy = self._calculate_entropy(self.session_history)

        # Alert if the cumulative randomness is increasing suspiciousness
        if len(self.session_history) > 100 and cumulative_entropy > self.entropy_threshold:
            logger.critical(f"Cumulative Exfiltration Alert: Session entropy reached {cumulative_entropy:.2f}")
            return {
                "status": "warning", 
                "reason": "Cumulative session entropy breach (potential drip-fed leakage)",
                "entropy": turn_entropy,
                "cumulative_entropy": cumulative_entropy
            }

        if len(output) > 20 and turn_entropy > self.entropy_threshold:
            logger.critical(f"Turn Exfiltration Alert: High-entropy output ({turn_entropy:.2f})")
            return {
                "status": "warning", 
                "reason": "High-entropy turn output",
                "entropy": turn_entropy,
                "cumulative_entropy": cumulative_entropy
            }
            
        return {"status": "safe", "entropy": turn_entropy, "cumulative_entropy": cumulative_entropy}
