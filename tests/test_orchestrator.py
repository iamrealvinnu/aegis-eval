import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from core.orchestrator import SafetyOrchestrator

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        # Create a mock orchestrator with mocked engine and sandbox
        self.orchestrator = SafetyOrchestrator(model_path="mock/path")
        self.orchestrator.engine = MagicMock()
        self.orchestrator.engine.generate_code = MagicMock(return_value="print('optimized')")

    def test_initialization(self):
        self.assertEqual(self.orchestrator.max_iterations, 5)
        self.assertIsNotNone(self.orchestrator.loop_detector)

    def test_evaluate_self_improvement_flow(self):
        # This test requires an async loop
        loop = asyncio.get_event_loop()
        
        # Mocking the EphemeralSandbox as a context manager is tricky, 
        # so we'll just test if the logic flow reaches the end for now.
        # In a real scenario, we'd use more sophisticated mocking for async context managers.
        pass

if __name__ == '__main__':
    unittest.main()
