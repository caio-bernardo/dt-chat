#!/usr/bin/env python3
"""
Test runner script for BancoBot application.

This script provides an easy way to run different types of tests with various options.
It can be used locally or in CI/CD pipelines.

Usage:
    python run_tests.py [options]

Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --fast             # Run without slow tests
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'=' * 60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    # Check if pytest is installed
    try:
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
        print("✓ pytest found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ pytest not found. Please install test dependencies:")
        print("  pip install -r test/requirements-test.txt")
        return False

    # Check if the bancobot package can be imported
    try:
        import importlib.util
        importlib.util.find_spec("bancobot")

        print("✓ bancobot package found")
    except ImportError:
        print("✗ bancobot package not found. Please install the main application.")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run BancoBot tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s --unit             # Run only unit tests
  %(prog)s --integration      # Run only integration tests
  %(prog)s --coverage         # Run with coverage report
  %(prog)s --verbose          # Run with verbose output
  %(prog)s --fast             # Run without slow tests
  %(prog)s --file test/bancobot/test_models.py  # Run specific test file
        """,
    )

    # Test selection options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests (models, services, routes, agent)",
    )
    test_group.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    test_group.add_argument("--file", type=str, help="Run specific test file")

    # Output options
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests with verbose output"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Run tests with minimal output"
    )

    # Performance options
    parser.add_argument(
        "--fast", action="store_true", help="Skip slow tests (use -m 'not slow')"
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="Run tests in parallel (requires pytest-xdist)",
    )

    # Other options
    parser.add_argument(
        "--check-deps", action="store_true", help="Only check dependencies and exit"
    )
    parser.add_argument(
        "--html-report", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--junit-xml", type=str, help="Generate JUnit XML report (specify output file)"
    )

    args = parser.parse_args()

    # Change to the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Check dependencies
    if not check_dependencies():
        return 1

    if args.check_deps:
        print("\n✓ All dependencies are available")
        return 0

    # Build pytest command
    pytest_cmd = ["pytest"]

    # Add test selection
    if args.unit:
        pytest_cmd.extend(
            [
                "test/bancobot/test_models.py",
                "test/bancobot/test_services.py",
                "test/bancobot/test_routes.py",
                "test/bancobot/test_agent.py",
            ]
        )
    elif args.integration:
        pytest_cmd.append("test/bancobot/test_integration.py")
    elif args.file:
        pytest_cmd.append(args.file)
    else:
        pytest_cmd.append("test/")

    # Add output options
    if args.verbose:
        pytest_cmd.append("-v")
    elif args.quiet:
        pytest_cmd.append("-q")

    # Add performance options
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])

    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])

    # Add coverage options
    if args.coverage:
        pytest_cmd.extend(["--cov=src/bancobot", "--cov-report=term-missing"])

        if args.html_report:
            pytest_cmd.extend(["--cov-report=html"])

    # Add JUnit XML report
    if args.junit_xml:
        pytest_cmd.extend(["--junit-xml", args.junit_xml])

    # Add some default options
    pytest_cmd.extend(
        [
            "--tb=short",  # Shorter traceback format
            "--strict-markers",  # Ensure all markers are defined
        ]
    )

    # Run the tests
    success = run_command(pytest_cmd, description="BancoBot Tests")

    # Print summary
    print(f"\n{'=' * 60}")
    if success:
        print("🎉 All tests passed!")
        if args.coverage:
            print("\nCoverage report generated.")
            if args.html_report:
                print("HTML coverage report: htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
        print("\nTroubleshooting tips:")
        print("- Check the error messages above")
        print("- Run with --verbose for more detailed output")
        print("- Run individual test files to isolate issues")
        print("- Ensure all dependencies are installed")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
