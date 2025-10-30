#!/usr/bin/env python3
"""
Test runner script for KarlCam API

This script provides convenient commands for running tests with various configurations
and generating coverage reports.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print its output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def run_unit_tests(verbose=False):
    """Run unit tests only"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "unit"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose=False):
    """Run integration tests only"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd, "Integration Tests")


def run_all_tests(verbose=False):
    """Run all tests"""
    cmd = ["python", "-m", "pytest", "tests/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd, "All Tests")


def run_tests_with_coverage(test_type="all", html=False, verbose=False):
    """Run tests with coverage reporting"""
    cmd = ["python", "-m", "pytest", "tests/", "--cov=.", "--cov-report=term-missing"]
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    
    if html:
        cmd.append("--cov-report=html")
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Tests with Coverage ({test_type})")


def run_coverage_report():
    """Generate and display coverage report"""
    cmd = ["python", "-m", "coverage", "report", "--show-missing"]
    return run_command(cmd, "Coverage Report")


def run_parallel_tests(workers=4, verbose=False):
    """Run tests in parallel"""
    cmd = ["python", "-m", "pytest", "tests/", "-n", str(workers)]
    if verbose:
        cmd.append("-v")
    return run_command(cmd, f"Parallel Tests ({workers} workers)")


def check_coverage_threshold(threshold=80):
    """Check if coverage meets minimum threshold"""
    cmd = ["python", "-m", "coverage", "report", "--fail-under", str(threshold)]
    result = run_command(cmd, f"Coverage Threshold Check ({threshold}%)")
    if result:
        print(f"✅ Coverage meets minimum threshold of {threshold}%")
    else:
        print(f"❌ Coverage below minimum threshold of {threshold}%")
    return result


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function"""
    cmd = ["python", "-m", "pytest", test_path]
    if verbose:
        cmd.append("-v")
    return run_command(cmd, f"Specific Test: {test_path}")


def run_failed_tests():
    """Re-run only the tests that failed in the last run"""
    cmd = ["python", "-m", "pytest", "--lf", "-v"]
    return run_command(cmd, "Failed Tests (last failed)")


def run_test_discovery():
    """Discover and list all available tests"""
    cmd = ["python", "-m", "pytest", "tests/", "--collect-only", "-q"]
    return run_command(cmd, "Test Discovery")


def clean_coverage_data():
    """Clean coverage data files"""
    coverage_files = [".coverage", "htmlcov/"]
    for file_path in coverage_files:
        path = Path(file_path)
        if path.is_file():
            path.unlink()
            print(f"Removed {file_path}")
        elif path.is_dir():
            import shutil
            shutil.rmtree(path)
            print(f"Removed directory {file_path}")


def main():
    """Main entry point for the test runner"""
    parser = argparse.ArgumentParser(description="KarlCam API Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Unit tests
    unit_parser = subparsers.add_parser("unit", help="Run unit tests only")
    
    # Integration tests  
    integration_parser = subparsers.add_parser("integration", help="Run integration tests only")
    
    # All tests
    all_parser = subparsers.add_parser("all", help="Run all tests")
    
    # Coverage tests
    coverage_parser = subparsers.add_parser("coverage", help="Run tests with coverage")
    coverage_parser.add_argument("--type", choices=["unit", "integration", "all"], 
                                default="all", help="Type of tests to run")
    coverage_parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    
    # Parallel tests
    parallel_parser = subparsers.add_parser("parallel", help="Run tests in parallel")
    parallel_parser.add_argument("-n", "--workers", type=int, default=4, 
                                help="Number of parallel workers")
    
    # Coverage report
    report_parser = subparsers.add_parser("report", help="Generate coverage report")
    
    # Coverage threshold check
    threshold_parser = subparsers.add_parser("threshold", help="Check coverage threshold")
    threshold_parser.add_argument("--min", type=int, default=80, 
                                help="Minimum coverage percentage")
    
    # Specific test
    specific_parser = subparsers.add_parser("test", help="Run specific test")
    specific_parser.add_argument("path", help="Path to test file or function")
    
    # Failed tests
    failed_parser = subparsers.add_parser("failed", help="Re-run failed tests")
    
    # Test discovery
    discover_parser = subparsers.add_parser("discover", help="Discover available tests")
    
    # Clean coverage data
    clean_parser = subparsers.add_parser("clean", help="Clean coverage data")
    
    # CI pipeline (comprehensive test suite)
    ci_parser = subparsers.add_parser("ci", help="Run full CI pipeline")
    ci_parser.add_argument("--threshold", type=int, default=80, 
                          help="Minimum coverage threshold for CI")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    success = True
    
    if args.command == "unit":
        success = run_unit_tests(args.verbose)
    
    elif args.command == "integration":
        success = run_integration_tests(args.verbose)
    
    elif args.command == "all":
        success = run_all_tests(args.verbose)
    
    elif args.command == "coverage":
        success = run_tests_with_coverage(args.type, args.html, args.verbose)
    
    elif args.command == "parallel":
        success = run_parallel_tests(args.workers, args.verbose)
    
    elif args.command == "report":
        success = run_coverage_report()
    
    elif args.command == "threshold":
        success = check_coverage_threshold(args.min)
    
    elif args.command == "test":
        success = run_specific_test(args.path, args.verbose)
    
    elif args.command == "failed":
        success = run_failed_tests()
    
    elif args.command == "discover":
        success = run_test_discovery()
    
    elif args.command == "clean":
        clean_coverage_data()
        print("Coverage data cleaned")
    
    elif args.command == "ci":
        print("Running full CI pipeline...")
        
        # Step 1: Clean previous data
        clean_coverage_data()
        
        # Step 2: Run all tests with coverage
        success = run_tests_with_coverage("all", html=True, verbose=args.verbose)
        
        if success:
            # Step 3: Check coverage threshold
            success = check_coverage_threshold(args.threshold)
        
        if success:
            print("\n🎉 CI Pipeline completed successfully!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print("\n💥 CI Pipeline failed!")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())