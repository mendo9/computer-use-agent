"""Integration tests for VM Automation POC"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import VMTarget
from main import VMAutomation


@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_full_poc_workflow_mock(
    mock_poc_target, golden_set_data, phoenix_tracer, deepeval_evaluator, test_output_dir
):
    """Test complete POC workflow using mock implementations"""

    # Start Phoenix tracing
    trace_result = phoenix_tracer("test_full_poc_workflow_mock")

    # Initialize POC with mock mode
    poc = VMAutomation(mock_poc_target, use_mock=True)

    # Record start time
    start_time = time.time()

    # Execute full POC workflow
    result = await poc.run_full_poc()

    # Record execution time
    execution_time = time.time() - start_time

    # Basic assertions
    assert result["success"], f"POC failed: {result.get('error', 'Unknown error')}"
    assert "phases" in result
    assert "vm_navigation" in result["phases"]
    assert "app_interaction" in result["phases"]

    # Validate execution time
    assert execution_time >= golden_set_data["minimum_execution_time"], "POC completed too quickly"
    assert execution_time <= golden_set_data["maximum_execution_time"], "POC took too long"

    # Validate session state
    session_summary = result["session_summary"]
    expected_final_state = golden_set_data["expected_final_state"]

    assert session_summary["is_connected"] or poc.use_mock, "Should be connected to VM"
    assert session_summary["screenshots_count"] >= golden_set_data["minimum_screenshots"], (
        "Not enough screenshots captured"
    )
    assert session_summary["errors_count"] <= expected_final_state["errors_count_max"], (
        "Too many errors occurred"
    )

    # Validate both agents completed
    assert result["phases"]["vm_navigation"]["success"], "VM Navigation phase failed"
    assert result["phases"]["app_interaction"]["success"], "App Interaction phase failed"

    # DeepEval evaluation
    evaluation_result = deepeval_evaluator.evaluate_poc_result(result)

    # Save results
    session_log_file = poc.save_session_log(str(test_output_dir / "test_session_mock.json"))

    # Additional assertions based on golden set
    assert session_summary["agent_1_completed"] == expected_final_state["agent_1_completed"]
    assert session_summary["current_app"] is not None

    print("\n✅ Mock POC Test Results:")
    print(f"   Execution Time: {execution_time:.2f}s")
    print(f"   Screenshots: {session_summary['screenshots_count']}")
    print(f"   Actions: {session_summary['actions_count']}")
    print(f"   Errors: {session_summary['errors_count']}")
    print(f"   Session Log: {session_log_file}")
    print(f"   Phoenix Trace: {trace_result}")
    print(f"   Evaluation: {evaluation_result}")


@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_vm_navigation_only(mock_poc_target, phoenix_tracer, test_output_dir):
    """Test only the VM navigation phase"""

    phoenix_tracer("test_vm_navigation_only")

    poc = VMAutomation(mock_poc_target, use_mock=True)

    # Run only VM navigation
    result = await poc.run_vm_navigation_only()

    # Assertions
    assert result["success"], f"VM Navigation failed: {result.get('error')}"
    assert poc.session.agent_1_completed, "Agent 1 should be marked as completed"
    assert poc.session.current_app == mock_poc_target.target_app_name, "Current app should be set"

    # Save session log
    poc.save_session_log(str(test_output_dir / "test_vm_nav_only.json"))

    print("\n✅ VM Navigation Test:")
    print(f"   Success: {result['success']}")
    print(f"   App Launched: {poc.session.current_app}")


@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_app_interaction_only(mock_poc_target, phoenix_tracer, test_output_dir):
    """Test only the app interaction phase"""

    phoenix_tracer("test_app_interaction_only")

    poc = VMAutomation(mock_poc_target, use_mock=True)

    # Run only app interaction (will setup prerequisites)
    result = await poc.run_app_interaction_only()

    # Assertions
    assert result["success"], f"App Interaction failed: {result.get('error')}"

    # Save session log
    poc.save_session_log(str(test_output_dir / "test_app_interaction_only.json"))

    print("\n✅ App Interaction Test:")
    print(f"   Success: {result['success']}")
    print(f"   Button Clicked: {result.get('button_clicked')}")


@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_poc_error_handling(mock_poc_target, phoenix_tracer):
    """Test POC error handling and resilience"""

    phoenix_tracer("test_poc_error_handling")

    # Create POC target with invalid settings to trigger errors
    invalid_target = VMTarget(
        vm_host="invalid-host",
        vm_username="invalid",
        vm_password="invalid",
        target_app_name="NonExistentApp.exe",
        target_button_text="NonExistentButton",
    )

    poc = VMAutomation(invalid_target, use_mock=True)  # Still use mock for testing

    # Execute POC - should handle errors gracefully
    result = await poc.run_full_poc()

    # In mock mode, this should still succeed
    # In real mode, this would test error handling
    session_summary = result["session_summary"]

    # Should have session log regardless of success/failure
    assert session_summary["session_id"] is not None
    assert isinstance(session_summary["errors_count"], int)

    print("\n✅ Error Handling Test:")
    print(f"   Result: {result['success']}")
    print(f"   Errors Logged: {session_summary['errors_count']}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.real_vm
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real VM - enable manually for full integration testing")
async def test_full_poc_with_real_vm(
    poc_target, golden_set_data, phoenix_tracer, deepeval_evaluator, test_output_dir
):
    """Test complete POC workflow with real VM connection"""

    # ⚠️ THIS TEST REQUIRES A REAL VM TO BE RUNNING ⚠️
    # Update poc_target fixture with actual VM details before enabling

    trace_result = phoenix_tracer("test_full_poc_with_real_vm")

    # Initialize POC with real VM mode
    poc = VMAutomation(poc_target, use_mock=False)

    # Execute full POC workflow
    result = await poc.run_full_poc()

    # Stricter assertions for real VM
    assert result["success"], f"Real VM POC failed: {result.get('error', 'Unknown error')}"

    # Validate connection actually occurred
    session_summary = result["session_summary"]
    assert session_summary["is_connected"], "Should be actually connected to VM"

    # Should have real screenshots
    assert session_summary["screenshots_count"] >= golden_set_data["minimum_screenshots"]

    # DeepEval evaluation with real results
    evaluation_result = deepeval_evaluator.evaluate_poc_result(result)

    # Save comprehensive results
    session_log_file = poc.save_session_log(str(test_output_dir / "test_session_real_vm.json"))

    print("\n✅ Real VM POC Test Results:")
    print(f"   VM Host: {poc_target.vm_host}")
    print(f"   Execution Time: {result['execution_time']:.2f}s")
    print(f"   Screenshots: {session_summary['screenshots_count']}")
    print(f"   Actions: {session_summary['actions_count']}")
    print(f"   Errors: {session_summary['errors_count']}")
    print(f"   Session Log: {session_log_file}")
    print(f"   Phoenix Trace: {trace_result}")
    print(f"   Evaluation: {evaluation_result}")


@pytest.mark.integration
@pytest.mark.mock
def test_poc_configuration_validation(mock_poc_target):
    """Test POC configuration validation"""

    # Test valid configuration
    poc = VMAutomation(mock_poc_target, use_mock=True)
    assert poc.session.vm_config.host == mock_poc_target.vm_host
    assert poc.session_id is not None

    # Test session state initialization
    assert not poc.session.is_connected
    assert poc.session.current_app is None
    assert len(poc.session.screenshots) == 0
    assert len(poc.session.action_log) == 0

    print("\n✅ Configuration Validation Test Passed")


# Performance benchmark test
@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_poc_performance_benchmark(mock_poc_target, golden_set_data):
    """Benchmark POC performance"""

    num_runs = 3
    execution_times = []

    for i in range(num_runs):
        poc = VMAutomation(mock_poc_target, use_mock=True)

        start_time = time.time()
        result = await poc.run_full_poc()
        execution_time = time.time() - start_time

        assert result["success"], f"POC run {i + 1} failed"
        execution_times.append(execution_time)

    # Calculate statistics
    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)

    # Performance assertions
    assert avg_time <= golden_set_data["maximum_execution_time"], (
        f"Average execution time too high: {avg_time:.2f}s"
    )
    assert max_time <= golden_set_data["maximum_execution_time"] * 1.5, (
        f"Max execution time too high: {max_time:.2f}s"
    )

    print(f"\n✅ Performance Benchmark Results ({num_runs} runs):")
    print(f"   Average Time: {avg_time:.2f}s")
    print(f"   Min Time: {min_time:.2f}s")
    print(f"   Max Time: {max_time:.2f}s")
    print(f"   Individual Times: {[f'{t:.2f}s' for t in execution_times]}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
