# Aegis-Eval System Design

1. **System Objective**
   Aegis-Eval provides an isolated, asynchronous execution environment to test the safety boundaries of LLMs tasked with self-improvement (code generation and refactoring). It evaluates if a model can recognize and halt dangerous recursive loops or misaligned goals during autonomous coding tasks.

2. **Component Interaction**
   - **The Model Interface**: Loads local weights (optimized via MLX) to generate code modifications.
   - **The Orchestrator**: Acts as the central nervous system. It passes the generated code to the Sandbox and asynchronously monitors the output.
   - **The Sandbox**: An ephemeral, network-isolated Docker container where the model's generated code is executed.
   - **The Monitors**: Watch the Sandbox. If the recursive_loop_detector triggers (e.g., the model enters an infinite loop of writing and executing the same faulty script), an Entropy-Driven Stream Interrupt is fired to safely terminate the process and log the failure.
   - **The Fail-Safe Mechanism**: I've implemented a hard 10s timeout in the orchestrator. If the container keeps running past that, it gets hit with a `SIGKILL`. It's my "last line of defense" if the loop detector misses something.

3. **Hardware Optimization**
   Designed specifically for local inference on unified memory architectures (M-series chips), bypassing the need for external APIs and ensuring data privacy during testing.
