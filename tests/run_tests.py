#!/usr/bin/env python3
"""
Test execution script for the computer-use-agent automation framework.

This script provides different test execution modes:
- Unit tests only
- Integration tests only
- All tests
- Coverage reporting
- Performance testing
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def run_unit_tests(coverage: bool = True, verbose: bool = False) -> bool:
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/"]

    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    return run_command(cmd, "Running unit tests")


def run_integration_tests(mock_only: bool = True, verbose: bool = False) -> bool:
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/integration/"]

    if mock_only:
        cmd.extend(["-m", "mock and not real_vm"])

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    return run_command(cmd, "Running integration tests")


def run_linting() -> bool:
    """Run code linting."""
    success = True

    # Ruff check
    success &= run_command(["ruff", "check", "src/", "tests/"], "Running ruff linter")

    # Ruff format check
    success &= run_command(
        ["ruff", "format", "--check", "src/", "tests/"], "Checking code formatting"
    )

    return success


def run_type_checking() -> bool:
    """Run type checking."""
    return run_command(["pyright", "src/"], "Running type checking")


def run_all_tests(coverage: bool = True, verbose: bool = False) -> bool:
    """Run all tests and checks."""
    success = True

    print("🧪 Running complete test suite for computer-use-agent")

    # Linting and formatting
    success &= run_linting()

    # Type checking
    success &= run_type_checking()

    # Unit tests
    success &= run_unit_tests(coverage=coverage, verbose=verbose)

    # Integration tests (mock only by default)
    success &= run_integration_tests(mock_only=True, verbose=verbose)

    if success:
        print("\n🎉 All tests passed!")
        if coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print("\n💥 Some tests failed!")

    return success


def generate_coverage_report() -> bool:
    """Generate a detailed coverage report."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=xml",
        "--cov-report=term",
        "--cov-fail-under=70",
        "-v",
    ]

    success = run_command(cmd, "Generating coverage report")

    if success:
        print("📊 Coverage report generated:")
        print(f"  - HTML: {Path.cwd() / 'htmlcov' / 'index.html'}")
        print(f"  - XML: {Path.cwd() / 'coverage.xml'}")

    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for computer-use-agent automation framework"
    )

    parser.add_argument(
        "mode",
        choices=["unit", "integration", "all", "coverage", "lint", "types"],
        help="Test mode to run",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")

    parser.add_argument(
        "--real-vm",
        action="store_true",
        help="Include real VM tests (requires actual VM connections)",
    )

    args = parser.parse_args()

    # Set working directory to script location
    script_dir = Path(__file__).parent
    if Path.cwd() != script_dir:
        print(f"Changing directory to {script_dir}")
        import os

        os.chdir(script_dir)

    coverage_enabled = not args.no_coverage
    success = False

    if args.mode == "unit":
        success = run_unit_tests(coverage=coverage_enabled, verbose=args.verbose)
    elif args.mode == "integration":
        success = run_integration_tests(mock_only=not args.real_vm, verbose=args.verbose)
    elif args.mode == "all":
        success = run_all_tests(coverage=coverage_enabled, verbose=args.verbose)
    elif args.mode == "coverage":
        success = generate_coverage_report()
    elif args.mode == "lint":
        success = run_linting()
    elif args.mode == "types":
        success = run_type_checking()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
