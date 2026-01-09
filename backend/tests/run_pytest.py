"""
Pytest Test Runner
Run all tests using pytest with coverage and detailed reporting
"""

import subprocess
import sys
from pathlib import Path


def run_pytest_suite():
    """Run complete pytest suite"""
    backend_dir = Path(__file__).parent.parent
    tests_dir = backend_dir / "tests"
    
    print("="*80)
    print("Running PyTest Suite with Coverage")
    print("="*80)
    print()
    
    # Pytest command with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "-v",                          # Verbose
        "--tb=short",                  # Short traceback
        "--cov=app",                   # Coverage for app directory
        "--cov-report=html",           # HTML coverage report
        "--cov-report=term-missing",   # Terminal report with missing lines
        "--timeout=30",                # 30 second timeout per test
        "-x",                          # Stop on first failure (remove to run all)
        "--durations=10",              # Show 10 slowest tests
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run pytest
    result = subprocess.run(cmd, cwd=backend_dir)
    
    return result.returncode


def run_specific_test_file(test_file: str):
    """Run a specific test file"""
    backend_dir = Path(__file__).parent.parent
    test_path = backend_dir / "tests" / test_file
    
    if not test_path.exists():
        print(f"Error: Test file not found: {test_path}")
        return 1
    
    print(f"Running: {test_file}")
    print("="*80)
    
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_path),
        "-v",
        "--tb=long",
        "--timeout=30"
    ]
    
    result = subprocess.run(cmd, cwd=backend_dir)
    
    return result.returncode


def run_by_marker(marker: str):
    """Run tests by pytest marker"""
    backend_dir = Path(__file__).parent.parent
    tests_dir = backend_dir / "tests"
    
    print(f"Running tests with marker: {marker}")
    print("="*80)
    
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "-v",
        "-m", marker,
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=backend_dir)
    
    return result.returncode


def show_coverage_report():
    """Open HTML coverage report"""
    backend_dir = Path(__file__).parent.parent
    htmlcov_dir = backend_dir / "htmlcov" / "index.html"
    
    if not htmlcov_dir.exists():
        print("Coverage report not found. Run tests first.")
        return 1
    
    import webbrowser
    webbrowser.open(str(htmlcov_dir))
    print(f"Opening coverage report: {htmlcov_dir}")
    
    return 0


def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    if not args or args[0] == "all":
        return run_pytest_suite()
    
    elif args[0] == "file" and len(args) > 1:
        return run_specific_test_file(args[1])
    
    elif args[0] == "marker" and len(args) > 1:
        return run_by_marker(args[1])
    
    elif args[0] == "coverage":
        return show_coverage_report()
    
    else:
        print("""
Usage: python run_pytest.py [command] [options]

Commands:
  all                  Run all tests with coverage (default)
  file <filename>      Run specific test file
  marker <marker>      Run tests with specific marker
  coverage             Open HTML coverage report

Examples:
  python run_pytest.py all
  python run_pytest.py file test_ocr_service.py
  python run_pytest.py marker asyncio
  python run_pytest.py coverage
""")
        return 1


if __name__ == "__main__":
    sys.exit(main())
