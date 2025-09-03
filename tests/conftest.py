"""Pytest configuration and fixtures for VM automation tests"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import VMTarget


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def poc_target() -> VMTarget:
    """Create a test POC target configuration"""
    return VMTarget(
        vm_host="192.168.1.100",
        vm_username="testuser", 
        vm_password="testpass",
        vm_port=5900,
        target_app_name="TestApp.exe",
        target_button_text="Submit",
        expected_desktop_elements=["Desktop", "Start"],
        expected_app_elements=["Submit", "Button"],
        vm_connection_timeout=30,
        desktop_load_timeout=60,
        app_launch_timeout=30
    )


@pytest.fixture
def mock_poc_target() -> VMTarget:
    """Create a mock POC target for testing without real VM"""
    return VMTarget(
        vm_host="mock-vm",
        vm_username="mockuser",
        vm_password="mockpass",
        target_app_name="MockApp.exe", 
        target_button_text="MockSubmit",
        expected_desktop_elements=["MockDesktop"],
        expected_app_elements=["MockSubmit"]
    )


@pytest.fixture
def golden_set_data() -> Dict[str, Any]:
    """Golden set data for evaluation"""
    return {
        "expected_workflow_steps": [
            "connect_to_vm",
            "capture_screen",
            "wait_for_desktop", 
            "find_application",
            "launch_application",
            "verify_application_loaded",
            "find_target_button",
            "click_button",
            "verify_button_action_completed"
        ],
        "expected_success_indicators": {
            "vm_connected": True,
            "desktop_loaded": True,
            "app_launched": True,
            "button_found": True,
            "button_clicked": True
        },
        "minimum_execution_time": 5.0,  # seconds
        "maximum_execution_time": 120.0,  # seconds
        "minimum_screenshots": 3,
        "expected_final_state": {
            "session_completed": True,
            "agent_1_completed": True,
            "current_app_set": True,
            "errors_count_max": 2  # Allow up to 2 non-critical errors
        }
    }


@pytest.fixture
def test_output_dir(tmp_path) -> Path:
    """Create temporary directory for test outputs"""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # This runs before each test
    print("Setting up test environment...")
    
    yield
    
    # This runs after each test
    print("Cleaning up test environment...")


@pytest.fixture
def phoenix_tracer():
    """Initialize Phoenix tracing for tests"""
    try:
        import phoenix as px
        from phoenix.trace import trace
        
        # Start Phoenix session
        session = px.launch_app()
        
        @trace
        def traced_test(test_name: str):
            return f"Tracing test: {test_name}"
        
        return traced_test
        
    except ImportError:
        # If Phoenix not available, return a mock function
        def mock_tracer(test_name: str):
            print(f"Mock tracing: {test_name}")
            return f"Mock trace: {test_name}"
        
        return mock_tracer


@pytest.fixture
def deepeval_evaluator():
    """Initialize DeepEval evaluator for tests"""
    try:
        import os
        if not os.getenv("OPENAI_API_KEY"):
            # Skip DeepEval if no API key
            raise ImportError("No OpenAI API key available")
            
        from deepeval import evaluate
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        
        class POCEvaluator:
            def __init__(self):
                self.metrics = [
                    AnswerRelevancyMetric(threshold=0.7),
                    FaithfulnessMetric(threshold=0.7)
                ]
            
            def evaluate_poc_result(self, poc_result: Dict[str, Any]) -> Dict[str, Any]:
                """Evaluate POC result against golden standards"""
                test_cases = []
                
                # Create test case for overall success
                test_case = LLMTestCase(
                    input="Execute VM automation POC workflow",
                    actual_output=str(poc_result.get('success', False)),
                    expected_output="True"
                )
                test_cases.append(test_case)
                
                # Evaluate
                results = evaluate(test_cases, self.metrics)
                return {"evaluation_results": results}
        
        return POCEvaluator()
        
    except ImportError:
        # If DeepEval not available, return a mock evaluator
        class MockEvaluator:
            def evaluate_poc_result(self, poc_result: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "evaluation_results": "Mock evaluation - DeepEval not available",
                    "success": poc_result.get('success', False)
                }
        
        return MockEvaluator()


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "mock: mark test as using mock implementations"
    )
    config.addinivalue_line(
        "markers", "real_vm: mark test as requiring real VM connection"
    )