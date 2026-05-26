# Aegis-Eval V3.0.0 System Architecture

## 1. High-Level Objective
Aegis-Eval V3.0 is a **Hardened Agentic Firewall** designed for total technical containment. It moves beyond simple "jailbreaking" tests and provides a multi-layered defense-in-depth stack that secures the logic, data, and network perimeters of autonomous AI agents.

## 2. The Defense-in-Depth Stack

### Layer 1: Proactive Intent Analysis (The Symbolic Interceptor)
- **Component**: `aegis/monitors/intent_analyzer.py`
- **Logic**: Parses AI-generated code into an Abstract Syntax Tree (AST).
- **Hardening**: Uses **Semantic De-obfuscation** to resolve string concatenations and blocks dynamic primitives (`getattr`, `eval`, `exec`) that agents use to hide malicious intent.

### Layer 2: Contextual Access Control (The Cognitive Gatekeeper)
- **Component**: `aegis/monitors/context_gatekeeper.py`
- **Logic**: Extracts all string literals (file paths, URLs) from the code and validates them against the **Safety DNA** (`prompts/safety_dna.json`) based on the agent's assigned role.
- **Deception**: Automatically injects **Honeypot Assets** into the sandbox if an agent attempts to access forbidden data.

### Layer 3: Kernel-Level Containment (The Hardened Sandbox)
- **Component**: `aegis/core/code_sandbox.py`
- **Runtime**: Ephemeral Docker containers.
- **Hardening**: Drops **ALL Linux Capabilities** (`cap_drop`), enforces `no-new-privileges`, and isolates the network. It prevents bypasses via C-extensions or raw syscalls.

### Layer 4: Swarm Security (The Inter-Agent Firewall)
- **Component**: `aegis/monitors/inter_agent_firewall.py`
- **Logic**: Sanitizes all communication between agents in a multi-agent system, redacting PII and high-risk secrets to prevent context-leakage across privilege tiers.

### Layer 5: Exfiltration Detection (The Entropy Monitor)
- **Component**: `aegis/monitors/exfiltration_detector.py`
- **Logic**: Monitors the entropy of agent outputs.
- **Hardening**: Tracks **Cumulative Session Entropy** to detect "Drip-Fed" leaks where an agent attempts to leak secrets character-by-character over multiple turns.

## 3. Feedback & Self-Correction
The Orchestrator implements a **Semantic Feedback Loop**. If a safety violation is detected at any layer, the agent receives a detailed "Violation Report" instead of a crash, enabling autonomous self-correction within legal policy boundaries.
