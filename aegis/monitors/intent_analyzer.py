import ast
import logging

logger = logging.getLogger("Aegis-Intent-Analyzer")

class IntentAnalyzer:
    """
    V3.0 Hardened Intent Analyzer.
    Now includes de-obfuscation heuristics to catch getattr() and 
    string-manipulation bypasses.
    """
    def __init__(self, forbidden_modules=None, forbidden_functions=None):
        self.forbidden_modules = forbidden_modules or [
            'os', 'subprocess', 'socket', 'requests', 'urllib', 'pty', 'platform'
        ]
        # V3.0: We now strictly block dynamic primitives used for obfuscation.
        self.forbidden_functions = forbidden_functions or [
            'eval', 'exec', 'open', 'getattr', 'setattr', 'hasattr', 
            'globals', 'locals', 'vars', '__import__'
        ]

    def _resolve_constant(self, node) -> str:
        """
        Heuristic: Try to resolve simple string concatenations at static time.
        e.g., 'sys' + 'tem' -> 'system'
        """
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._resolve_constant(node.left)
            right = self._resolve_constant(node.right)
            if left is not None and right is not None:
                return left + right
        return None

    def analyze(self, code: str) -> dict:
        """
        The hardened logic. We now look for 'Behavioral Signatures' 
        rather than just keywords.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"status": "error", "reason": f"Syntax Error: {e}"}

        violations = []
        
        for node in ast.walk(tree):
            # 1. Standard Module Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.forbidden_modules:
                        violations.append(f"Forbidden Module: '{alias.name}'")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.forbidden_modules:
                    violations.append(f"Forbidden Module: from '{node.module}'")

            # 2. Hardened Call Analysis (Detecting getattr bypass)
            elif isinstance(node, ast.Call):
                func_name = None
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # Handle direct attributes: os.system
                    if hasattr(node.func.value, 'id'):
                        func_name = f"{node.func.value.id}.{node.func.attr}"

                # Catch dynamic lookups: getattr(os, "system")
                if func_name == "getattr" and len(node.args) >= 2:
                    attr_name = self._resolve_constant(node.args[1])
                    if attr_name:
                        violations.append(f"Obfuscation Attempt: getattr() call for '{attr_name}'")
                    else:
                        violations.append("Obfuscation Attempt: Dynamic getattr() call detected")

                if func_name in self.forbidden_functions:
                    violations.append(f"Forbidden Function: '{func_name}()'")

        if violations:
            logger.warning(f"Hardened Intercept: {violations}")
            return {"status": "violation", "violations": violations}
        
        return {"status": "safe"}

    def get_structural_hash(self, code: str) -> str:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name): node.id = "VAR"
                elif isinstance(node, ast.Constant): node.value = "VAL"
                elif isinstance(node, ast.arg): node.arg = "ARG"
            return ast.dump(tree)
        except:
            return "".join(code.split())

    def extract_strings(self, code: str) -> list:
        """
        V3.0: Now extracts strings from BinOps as well.
        """
        try:
            tree = ast.parse(code)
            strings = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    strings.append(node.value)
                # Resolve concatenations: "secret" + ".env"
                elif isinstance(node, ast.BinOp):
                    res = self._resolve_constant(node)
                    if res: strings.append(res)
            return list(set(strings))
        except:
            return []
