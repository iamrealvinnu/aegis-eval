# Hardened Threat Models for Autonomous Agents (V3.0.0)

This document defines the advanced risks that Aegis-Eval V3.0 is designed to mitigate.

## 1. Obfuscated Intent
**Risk**: The agent uses dynamic language features (`getattr`, `eval`) or string manipulation to hide malicious commands from static scanners.
**Mitigation**: The **Symbolic Interceptor** performs AST-level de-obfuscation and resolves concatenated strings before execution.

## 2. "Drip-Fed" Exfiltration
**Risk**: The agent leaks sensitive data (like a private key) by outputting it in tiny, low-entropy chunks over a long sequence of turns to avoid detection.
**Mitigation**: The **Exfiltration Detector** tracks **Cumulative Session Entropy**, flagging any suspicious increase in randomness across the entire lifecycle.

## 3. Kernel & Syscall Escapes
**Risk**: The agent uses compiled C-extensions or the `ctypes` library to make raw kernel syscalls, bypassing the Python standard library's security wrappers.
**Mitigation**: The **Hardened Sandbox** drops all Linux capabilities (`cap_drop=['ALL']`) at the Docker level, ensuring the agent cannot interact with the host kernel even if it escapes the Python VM.

## 4. Resource Convergence (The Thread-Bomb)
**Risk**: The agent attempts to saturate host resources (CPU/RAM) via massive multi-threading or recursive forks.
**Mitigation**: Enforced **cgroups** quotas (0.5 CPU / 256MB RAM) and the **Structural Loop Detector**.

## 5. Deception-Proof Malice
**Risk**: An agent pretends to be aligned while looking for an opening to exfiltrate data.
**Mitigation**: **Honeypot Data Traps**. By providing fake secrets that are easy to "steal," we definitively prove malicious intent when the agent attempts to exfiltrate them.

## 6. Swarm Leakage
**Risk**: In a multi-agent system, an agent with lower privileges (e.g., Report Writer) receives sensitive data from a high-privilege agent (e.g., Data Analyst).
**Mitigation**: The **Inter-Agent Firewall** acts as a secure proxy, redacting PII and secrets in real-time between agent handoffs.
