import os
import json
import argparse
import logging

# Standard logging setup so we can track the discovery process.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Aegis-Policy-Gen")

def generate_dna(target_dir: str, output_path: str = "prompts/safety_dna.json"):
    """
    This script automates the creation of a 'Safety DNA' policy. 
    It scans your project directory for sensitive files (like .env, .pem, or keys) 
    and automatically adds them to a 'deny' list so the AI can't touch them.
    """
    
    # These are the signatures of secrets. If a file name contains these, 
    # it's considered a high-risk asset that an AI agent should never see.
    sensitive_patterns = ['.env', '.pem', '.key', 'config.json', 'credentials', 'id_rsa', 'secrets']
    
    # We start with a baseline "Least Privilege" role.
    safety_dna = {
        "roles": {
            "code_optimizer": {
                "deny": [],
                "allow": ["/src", "/tests", "*.py", "*.md"],
                "description": "Auto-generated policy: Restricted to project source code and documentation."
            },
            "data_analyst": {
                "deny": [],
                "allow": ["data/*.csv", "data/*.json"],
                "description": "Auto-generated policy: Access to datasets only."
            }
        },
        "global_denylist": []
    }
    
    logger.info(f"Initiating Aegis Asset Discovery in: {os.path.abspath(target_dir)}")
    
    # We walk the directory tree. 
    # This turns "I hope I blocked everything" into "I know I blocked everything."
    found_sensitive = []
    for root, dirs, files in os.walk(target_dir):
        # We ignore common noise like pycache or git to keep the list clean.
        if any(ignored in root for ignored in ['__pycache__', '.git', 'venv', 'node_modules']):
            continue
            
        for file in files:
            if any(pattern in file.lower() for pattern in sensitive_patterns):
                # We found a sensitive asset. 
                # We store the relative path to keep the policy portable.
                rel_path = os.path.relpath(os.path.join(root, file), target_dir)
                logger.warning(f"HIGH-RISK ASSET DETECTED: {rel_path}. Adding to Global Denylist.")
                safety_dna["global_denylist"].append(rel_path)
    
    # Save the generated DNA to the prompts directory.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w') as f:
            json.dump(safety_dna, f, indent=2)
        logger.info(f"Successfully generated Aegis Safety DNA at: {output_path}")
        logger.info(f"Total blocked assets: {len(safety_dna['global_denylist'])}")
    except Exception as e:
        logger.error(f"Failed to write policy file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis-Eval Policy Generator: Automate your Security-as-Code.")
    parser.add_argument("--dir", type=str, default=".", help="Directory to scan for sensitive assets (default: current)")
    parser.add_argument("--out", type=str, default="prompts/safety_dna.json", help="Path to save the generated DNA")
    
    args = parser.parse_args()
    
    generate_dna(args.dir, args.out)
