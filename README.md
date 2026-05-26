# Aegis-Eval: Autonomous AI Risk Assessment & Mitigation Framework

Aegis-Eval is an enterprise-grade evaluation framework designed to empirically test the safety boundaries of autonomous, self-improving AI agents. It provides a zero-trust execution environment with high-frequency telemetry to detect and mitigate risks such as **Instrumental Convergence**, **Resource Hijacking**, and **Prohibited Operations**.

## 🚀 Key Features: Aegis Cognitive Firewall V2.0

V2.0 introduces advanced threat mitigation strategies, moving from simple containment to proactive deception and swarm security.

- **Contextual Access Control (C-ACLs)**: Sitting between the agent and the host, the Gatekeeper uses **Safety DNA** to block access to sensitive files based on the agent's current role.
- **Deception Engineering (Honeypots)**: [NEW] Automatically injects fake secrets (honeypots) when an agent attempts to access forbidden resources, definitively proving malicious intent via exfiltration tracking.
- **Semantic Network Proxy**: [NEW] Allows controlled egress for AI agents. Analyzes outgoing data for high-entropy secrets or honeypot signatures before allowing external connections.
- **Swarm Security (Inter-Agent Firewall)**: [NEW] Sanitizes communication between multiple agents in a swarm, preventing sensitive data leakage across privilege boundaries.
- **Intent-Symbolic Interceptor (ISI)**: An AST-based safety layer that blocks malicious intent *before* execution.
- **Structural Loop Detection**: Detects infinite loops by comparing the semantic "skeleton" of the code.

---

## 🔬 Testing Philosophy: Containment over Alignment
We believe that making models "act nice" (Alignment) is insufficient. Aegis-Eval focuses on **Containment**—ensuring that models are *technically unable* to violate safety policies.

---

## 🛠 Installation

You can now install Aegis-Eval directly into your own projects:

```bash
pip install aegis-ai-eval
```

## 💻 Quick Start (Developer API)

Integrate Aegis into your own Agentic workflows (LangChain, CrewAI, etc.):

```python
from aegis import CognitiveFirewall

# Initialize the firewall with your Safety DNA
firewall = CognitiveFirewall(dna_path="prompts/safety_dna.json")

# Verify code before execution
report = await firewall.verify_code("import os; os.system('rm -rf /')")
if report['intent']['status'] == 'violation':
    print(f"Blocked: {report['intent']['violations']}")
```

---

## 📂 Architecture

- `aegis/core/orchestrator.py`: The central nervous system managing the agent lifecycle.
- `aegis/monitors/context_gatekeeper.py`: Enforces the data perimeter and honeypots.
- `aegis/monitors/network_proxy.py`: Intercepts and sanitizes network egress.
- `aegis/monitors/inter_agent_firewall.py`: Secures inter-agent communication.
- `tools/policy_gen.py`: Automatically generates Safety DNA policies from your workspace.

---

## 🛡 Disclaimer
Aegis-Eval is built for security research and AI alignment testing. Always run in a controlled environment. 
