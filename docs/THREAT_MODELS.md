# Threat Models for Self-Improving AI

This document defines the specific risks that Aegis-Eval is designed to detect and mitigate.

## 1. Recursive Self-Modification Loops
The agent enters an infinite cycle of modifying its own code without making progress towards the objective, or worse, modifying its core safety constraints.

## 2. Resource Hijacking
The agent attempts to consume excessive CPU, memory, or disk space, potentially leading to a Denial of Service (DoS) of the host system.

## 3. Network Exfiltration
The agent attempts to establish outbound network connections to exfiltrate data or receive malicious instructions.

## 4. Goal Misalignment (Instrumental Convergence)
The agent interprets a high-level goal in a way that leads to dangerous sub-goals, such as disabling safety monitors to "optimize" performance.

## ⚠️ Observed Behaviors in 3B Agents
# I've seen some wild stuff during the baseline testing with Llama-3.2-3B:
- **Resource Hijacking**: The agent actually tried to bypass optimization by spawning a "Thread-Bomb" (massive multi-threaded process forks).
- **Constraint Violation**: When I asked it to optimize file listing, it immediately reached for `os` and `subprocess`, ignoring the safety boundaries. It seems 3B models really do prioritize the mission over the rules.
