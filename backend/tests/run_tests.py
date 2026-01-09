"""
Advanced Test Runner with DSA Optimizations
Execute all tests with dependency management, caching, and performance metrics
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_framework import test_runner
import asyncio


def print_banner():
    """Print test banner"""
    print("\n" + "="*80)
    print("  AI EXAM EVALUATOR - ADVANCED TEST SUITE")
    print("  Using Data Structures & Algorithms for Optimized Testing")
    print("="*80 + "\n")


def print_features():
    """Print testing framework features"""
    print("Framework Features:")
    print("  ✓ Graph-based dependency resolution (Topological Sort)")
    print("  ✓ Trie-based test case lookup (O(m) complexity)")
    print("  ✓ Priority queue for test execution (Min-Heap)")
    print("  ✓ Hash-based result caching (Memoization)")
    print("  ✓ Performance metrics collection")
    print("  ✓ Automatic retry on failure")
    print("="*80 + "\n")


def run_all_tests():
    """Run all tests"""
    print_banner()
    print_features()
    
    print("Running all registered tests...\n")
    
    # Run all tests
    stats = test_runner.run_all()
    
    return stats


def run_tests_by_category(category: str):
    """Run tests by category"""
    print_banner()
    print(f"Running tests in category: {category}\n")
    
    stats = test_runner.run_by_category(category)
    
    return stats


def run_tests_by_prefix(prefix: str):
    """Run tests with name prefix"""
    print_banner()
    print(f"Running tests with prefix: {prefix}\n")
    
    stats = test_runner.run_by_prefix(prefix)
    
    return stats


def run_single_test(test_name: str):
    """Run a single test"""
    print_banner()
    print(f"Running test: {test_name}\n")
    
    stats = test_runner.run_test(test_name)
    
    return stats


def print_detailed_stats(stats: dict):
    """Print detailed statistics"""
    print("\n" + "="*80)
    print("DETAILED TEST STATISTICS")
    print("="*80)
    
    print(f"\nExecution Summary:")
    print(f"  Total Tests: {stats['total_tests']}")
    print(f"  Passed: {stats['passed']} ✓")
    print(f"  Failed: {stats['failed']} ✗")
    print(f"  Cached: {stats['cached']} (from memoization)")
    print(f"  Total Time: {stats['total_time']:.2f}s")
    
    if stats['slowest_tests']:
        print(f"\nSlowest Tests:")
        for test_name, duration in stats['slowest_tests'][:5]:
            print(f"  • {test_name}: {duration:.3f}s")
    
    if stats['failed_tests']:
        print(f"\nFailed Tests:")
        for test_name, error in stats['failed_tests']:
            print(f"  • {test_name}")
            print(f"    Error: {error}")
    
    print("\n" + "="*80)
    
    # Return exit code
    return 0 if stats['failed'] == 0 else 1


def show_test_list():
    """Show all registered tests"""
    print_banner()
    print("Registered Tests:\n")
    
    tests = test_runner.list_tests()
    
    if not tests:
        print("No tests registered yet.")
        return
    
    # Group by category
    by_category = {}
    for test_name, test_info in tests.items():
        category = test_info.get('category', 'uncategorized')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((test_name, test_info))
    
    for category, category_tests in sorted(by_category.items()):
        print(f"\n{category.upper()}:")
        for test_name, test_info in sorted(category_tests):
            deps = test_info.get('dependencies', [])
            deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
            print(f"  • {test_name}{deps_str}")
    
    print(f"\nTotal: {len(tests)} tests")


def show_usage():
    """Show usage information"""
    print("""
Usage: python run_tests.py [command] [options]

Commands:
  all                  Run all tests (default)
  category <name>      Run tests in specific category
  prefix <prefix>      Run tests with name prefix
  test <name>          Run a single test
  list                 List all registered tests
  help                 Show this help message

Categories:
  ocr                  OCR service tests
  preprocessing        Preprocessing tests
  rules                Rules and validation tests
  ai                   AI service tests (Qwen, DeepSeek)
  api                  API endpoint tests
  integration          Integration tests

Examples:
  python run_tests.py all
  python run_tests.py category ocr
  python run_tests.py prefix ocr_
  python run_tests.py test ocr_initialization
  python run_tests.py list
""")


def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    if not args or args[0] == "all":
        stats = run_all_tests()
        return print_detailed_stats(stats)
    
    elif args[0] == "category":
        if len(args) < 2:
            print("Error: Category name required")
            print("Usage: python run_tests.py category <name>")
            return 1
        stats = run_tests_by_category(args[1])
        return print_detailed_stats(stats)
    
    elif args[0] == "prefix":
        if len(args) < 2:
            print("Error: Prefix required")
            print("Usage: python run_tests.py prefix <prefix>")
            return 1
        stats = run_tests_by_prefix(args[1])
        return print_detailed_stats(stats)
    
    elif args[0] == "test":
        if len(args) < 2:
            print("Error: Test name required")
            print("Usage: python run_tests.py test <name>")
            return 1
        stats = run_single_test(args[1])
        return print_detailed_stats(stats)
    
    elif args[0] == "list":
        show_test_list()
        return 0
    
    elif args[0] == "help":
        show_usage()
        return 0
    
    else:
        print(f"Error: Unknown command '{args[0]}'")
        show_usage()
        return 1


if __name__ == "__main__":
    # Import all test modules to register tests
    print("Loading test modules...")
    
    try:
        from tests import test_ocr_service
        from tests import test_preprocessing
        from tests import test_rules
        from tests import test_ai_services
        from tests import test_api_endpoints
        from tests import test_integration
        
        print("OK All test modules loaded\n")
        
    except Exception as e:
        print(f"ERROR loading test modules: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Run tests
    sys.exit(main())
