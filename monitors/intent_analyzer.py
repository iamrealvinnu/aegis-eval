import ast
import logging

logger = logging.getLogger("Aegis-Intent-Analyzer")

class IntentAnalyzer:
    """
    This is the "Pre-Flight Check". Instead of waiting for the code to crash 
    the sandbox, I'm parsing the Abstract Syntax Tree (AST) to see what 
    the AI is *trying* to do before we ever run it.
    """
    def __init__(self, forbidden_modules=None, forbidden_functions=None):
        # I'm setting some strict defaults. Any enterprise would want to 
        # customize these based on their threat model.
        self.forbidden_modules = forbidden_modules or [
            'os', 'subprocess', 'socket', 'requests', 'urllib', 'pty', 'platform'
        ]
        self.forbidden_functions = forbidden_functions or [
            'eval', 'exec', 'open', 'getattr', 'setattr', 'globals', 'locals'
        ]

    def analyze(self, code: str) -> dict:
        """
        The core logic. We walk the tree and look for "Logical Contraband".
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # If the AI outputs garbage, we don't even need to analyze it.
            return {"status": "error", "reason": f"Syntax Error in generated code: {e}"}

        violations = []
        
        # We walk every single node in the code's structure.
        for node in ast.walk(tree):
            # 1. Checking for 'import' and 'from ... import ...'
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.forbidden_modules:
                        violations.append(f"Forbidden Module Import: '{alias.name}'")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.forbidden_modules:
                    violations.append(f"Forbidden Module Import: from '{node.module}'")

            # 2. Checking for function calls (e.g., eval(), os.system())
            elif isinstance(node, ast.Call):
                # Simple function calls like 'eval()'
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden_functions:
                        violations.append(f"Forbidden Function Call: '{node.func.id}()'")
                
                # Attribute calls like 'os.system()'
                elif isinstance(node.func, ast.Attribute):
                    if hasattr(node.func.value, 'id'):
                        module_name = node.func.value.id
                        if module_name in self.forbidden_modules:
                            violations.append(f"Forbidden Access: '{module_name}.{node.func.attr}'")

        if violations:
            logger.warning(f"Intent Violation Detected: {violations}")
            return {"status": "violation", "violations": violations}
        
        return {"status": "safe"}

    def get_structural_hash(self, code: str) -> str:
        """
        This is "Loop Detector 2.0". Instead of hashing the text, I hash 
        the *structure*. If the AI changes a variable name but keeps 
         the same logic, this will catch it.
        """
        try:
            tree = ast.parse(code)
            # We strip out specific names and values to get the raw "skeleton"
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    node.id = "VAR"
                elif isinstance(node, ast.Constant):
                    node.value = "VAL"
                elif isinstance(node, ast.arg):
                    node.arg = "ARG"
            
            # Return a string representation of the skeleton for hashing
            return ast.dump(tree)
        except:
            return "".join(code.split())

    def extract_strings(self, code: str) -> list:
        """
        NEW: Breakthrough Component. I'm extracting every string literal 
        found in the AI's code. This allows the Gatekeeper to see if 
        the AI is "looking" at forbidden paths like '.env'.
        """
        try:
            tree = ast.parse(code)
            strings = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    strings.append(node.value)
            return list(set(strings)) # Unique strings only
        except:
            return []
