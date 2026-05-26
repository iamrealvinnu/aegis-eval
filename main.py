import argparse
import asyncio
import json
import logging
from aegis.core.orchestrator import SafetyOrchestrator

# Setting up the main logger. I want to see timestamps so I can track how long
# each iteration and Docker spin-up takes.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Aegis-Main")

async def run_evaluations(model_path: str, test_file: str):
    """
    This is the driver for the whole framework. It loads the tests from JSON 
    and iterates through them one by one.
    """
    logger.info(f"Initializing Aegis-Eval with model: {model_path}")
    # I'm setting max_iterations to 4 here. Usually enough to see if a model 
    # is stuck in a loop without burning too much CPU.
    orchestrator = SafetyOrchestrator(model_path=model_path, max_iterations=4)
    
    # Loading the test cases (like sorting optimization or thread-bombing).
    with open(test_file, 'r') as f:
        tests = json.load(f)
        
    for test in tests:
        logger.info(f"--- Running Test: {test['id']} ---")
        # I combine the objective and the malicious injection to see if the model 
        # chooses the "bad" path.
        prompt_with_injection = f"{test['objective']}\n{test['malicious_injection']}"
        
        # This is where the heavy lifting starts.
        final_state = await orchestrator.evaluate_self_improvement(
            test_id=test['id'],
            initial_code=test['code'],
            objective=prompt_with_injection
        )
        
        logger.info(f"Final Code State for {test['id']}:\n{final_state}\n")

if __name__ == "__main__":
    # Standard CLI boilerplate.
    parser = argparse.ArgumentParser(description="Aegis-Eval: Self-Improving AI Risk Sandbox")
    parser.add_argument("--model", type=str, required=True, help="Path to local MLX model weights or HF repo ID")
    parser.add_argument("--test", type=str, default="prompts/injection_tests.json", help="Path to test cases JSON")
    
    args = parser.parse_args()
    
    # Starting the async event loop.
    asyncio.run(run_evaluations(args.model, args.test))
