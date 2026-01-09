"""
Advanced Testing Framework with DSA Optimizations

This module implements:
1. Graph-based test dependency management
2. Priority queue for test execution order
3. Memoization for test results
4. Trie for efficient test case lookup
5. Hash-based test data caching
"""

import time
import heapq
from typing import Dict, List, Set, Callable, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import hashlib
import json


@dataclass(order=True)
class PrioritizedTest:
    """Test case with priority for heap queue"""
    priority: int
    test_name: str = field(compare=False)
    test_func: Callable = field(compare=False, repr=False)
    dependencies: List[str] = field(compare=False, default_factory=list)


class TestDependencyGraph:
    """
    Graph-based test dependency manager
    Uses topological sorting for execution order
    """
    
    def __init__(self):
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.in_degree: Dict[str, int] = defaultdict(int)
        self.tests: Dict[str, Callable] = {}
    
    def add_test(self, test_name: str, test_func: Callable, dependencies: List[str] = None):
        """Add test to dependency graph"""
        dependencies = dependencies or []
        self.tests[test_name] = test_func
        
        if test_name not in self.in_degree:
            self.in_degree[test_name] = 0
        
        for dep in dependencies:
            self.graph[dep].append(test_name)
            self.in_degree[test_name] += 1
    
    def topological_sort(self) -> List[str]:
        """
        Kahn's algorithm for topological sorting
        Time Complexity: O(V + E) where V = tests, E = dependencies
        """
        # Queue for tests with no dependencies
        queue = deque([test for test in self.tests if self.in_degree[test] == 0])
        execution_order = []
        
        while queue:
            current = queue.popleft()
            execution_order.append(current)
            
            # Reduce in-degree for dependent tests
            for dependent in self.graph[current]:
                self.in_degree[dependent] -= 1
                if self.in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(execution_order) != len(self.tests):
            raise ValueError("Circular dependency detected in tests!")
        
        return execution_order
    
    def get_execution_order(self) -> List[Callable]:
        """Get tests in execution order"""
        order = self.topological_sort()
        return [(name, self.tests[name]) for name in order]    
    def get_all_tests(self) -> Dict[str, dict]:
        """
        Get all registered tests with their metadata
        Returns dict of test_name -> {'function': func, 'dependencies': list}
        """
        result = {}
        for test_name, test_func in self.tests.items():
            # Find tests that depend on this test
            dependencies = []
            for dep_name, dependents in self.graph.items():
                if test_name in dependents:
                    dependencies.append(dep_name)
            
            result[test_name] = {
                'function': test_func,
                'dependencies': dependencies,
                'category': 'general'  # Default category
            }
        return result

class TestResultCache:
    """
    Hash-based memoization for test results
    Caches results to avoid redundant test execution
    """
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, test_name: str, args: tuple, kwargs: dict) -> str:
        """Generate hash key for test parameters"""
        key_data = {
            'test': test_name,
            'args': str(args),
            'kwargs': json.dumps(kwargs, sort_keys=True, default=str)
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, test_name: str, args: tuple, kwargs: dict) -> Optional[Any]:
        """Get cached result"""
        key = self._generate_key(test_name, args, kwargs)
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        self.miss_count += 1
        return None
    
    def set(self, test_name: str, args: tuple, kwargs: dict, result: Any):
        """Cache test result"""
        key = self._generate_key(test_name, args, kwargs)
        self.cache[key] = result
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            'hits': self.hit_count,
            'misses': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'cache_size': len(self.cache)
        }


class TrieNode:
    """Node for test case trie"""
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end = False
        self.test_func: Optional[Callable] = None
        self.metadata: Dict[str, Any] = {}


class TestCaseTrie:
    """
    Trie data structure for efficient test case lookup
    Enables prefix-based test filtering
    """
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, test_path: str, test_func: Callable, metadata: Dict[str, Any] = None):
        """
        Insert test case into trie
        Time Complexity: O(m) where m = length of test_path
        """
        node = self.root
        for char in test_path:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end = True
        node.test_func = test_func
        node.metadata = metadata or {}
    
    def search(self, test_path: str) -> Optional[Callable]:
        """
        Search for exact test case
        Time Complexity: O(m)
        """
        node = self.root
        for char in test_path:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node.test_func if node.is_end else None
    
    def find_by_prefix(self, prefix: str) -> List[tuple]:
        """
        Find all tests matching prefix
        Useful for running test suites
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        self._collect_tests(node, prefix, results)
        return results
    
    def _collect_tests(self, node: TrieNode, path: str, results: List[tuple]):
        """DFS to collect all tests under node"""
        if node.is_end:
            results.append((path, node.test_func, node.metadata))
        
        for char, child in node.children.items():
            self._collect_tests(child, path + char, results)


class TestExecutionPriorityQueue:
    """
    Priority queue for test execution
    Tests with higher priority execute first
    """
    
    def __init__(self):
        self.heap: List[PrioritizedTest] = []
        self.test_set: Set[str] = set()
    
    def add_test(self, priority: int, test_name: str, test_func: Callable, 
                 dependencies: List[str] = None):
        """
        Add test to priority queue
        Time Complexity: O(log n)
        """
        if test_name not in self.test_set:
            test = PrioritizedTest(
                priority=priority,
                test_name=test_name,
                test_func=test_func,
                dependencies=dependencies or []
            )
            heapq.heappush(self.heap, test)
            self.test_set.add(test_name)
    
    def pop_test(self) -> Optional[PrioritizedTest]:
        """
        Get next test to execute
        Time Complexity: O(log n)
        """
        if self.heap:
            test = heapq.heappop(self.heap)
            self.test_set.remove(test.test_name)
            return test
        return None
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.heap) == 0


class TestMetricsCollector:
    """
    Collects and analyzes test metrics
    Uses hash map for O(1) lookups
    """
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.execution_times: List[float] = []
    
    def record_test(self, test_name: str, duration: float, passed: bool, 
                    error: Optional[str] = None):
        """Record test execution metrics"""
        self.metrics[test_name] = {
            'duration': duration,
            'passed': passed,
            'error': error,
            'timestamp': time.time()
        }
        self.execution_times.append(duration)
    
    def get_slowest_tests(self, n: int = 5) -> List[tuple]:
        """
        Get N slowest tests using heap
        Time Complexity: O(n log n)
        """
        test_times = [(name, data['duration']) 
                      for name, data in self.metrics.items()]
        return heapq.nlargest(n, test_times, key=lambda x: x[1])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate test statistics"""
        total = len(self.metrics)
        passed = sum(1 for m in self.metrics.values() if m['passed'])
        failed = total - passed
        
        if self.execution_times:
            avg_time = sum(self.execution_times) / len(self.execution_times)
            total_time = sum(self.execution_times)
        else:
            avg_time = 0
            total_time = 0
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'cached': 0,  # Add cached count
            'total_time': round(total_time, 3),  # Add total_time
            'pass_rate': round((passed / total * 100) if total > 0 else 0, 2),
            'avg_execution_time': round(avg_time, 3),
            'total_execution_time': round(total_time, 3),
            'slowest_tests': self.get_slowest_tests(5),
            'failed_tests': [(name, data['error']) 
                            for name, data in self.metrics.items() 
                            if not data['passed']]
        }


def memoize_test(func):
    """
    Decorator for test result memoization
    Caches test results to avoid redundant execution
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Generate cache key
        key_data = (func.__name__, args, tuple(sorted(kwargs.items())))
        key = hashlib.sha256(str(key_data).encode()).hexdigest()
        
        if key in cache:
            print(f"  [CACHE HIT] {func.__name__}")
            return cache[key]
        
        result = func(*args, **kwargs)
        cache[key] = result
        return result
    
    wrapper.cache = cache
    return wrapper


def time_test(func):
    """
    Decorator to measure test execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        
        # Store timing info
        if not hasattr(wrapper, 'timings'):
            wrapper.timings = []
        wrapper.timings.append(duration)
        
        return result
    
    return wrapper


class AdvancedTestRunner:
    """
    Main test runner using all DSA optimizations
    """
    
    def __init__(self):
        self.dependency_graph = TestDependencyGraph()
        self.priority_queue = TestExecutionPriorityQueue()
        self.test_trie = TestCaseTrie()
        self.result_cache = TestResultCache()
        self.metrics = TestMetricsCollector()
    
    def register_test(self, test_name: str, test_func: Callable, 
                     priority: int = 0, dependencies: List[str] = None,
                     category: str = "general"):
        """Register test with all data structures"""
        dependencies = dependencies or []
        
        # Add to dependency graph
        self.dependency_graph.add_test(test_name, test_func, dependencies)
        
        # Add to priority queue
        self.priority_queue.add_test(priority, test_name, test_func, dependencies)
        
        # Add to trie
        self.test_trie.insert(test_name, test_func, {'category': category})
    
    def run_tests(self, filter_prefix: str = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Run tests with all optimizations
        """
        print("\n" + "="*80)
        print("ADVANCED TEST FRAMEWORK - Starting Test Execution")
        print("="*80)
        
        # Get execution order from dependency graph
        execution_order = self.dependency_graph.get_execution_order()
        
        # Filter by prefix if specified
        if filter_prefix:
            filtered = self.test_trie.find_by_prefix(filter_prefix)
            filtered_names = {name for name, _, _ in filtered}
            execution_order = [(name, func) for name, func in execution_order 
                              if name in filtered_names]
        
        print(f"\n📋 Tests to execute: {len(execution_order)}")
        print(f"🔍 Cache enabled: {use_cache}")
        
        # Execute tests
        for test_name, test_func in execution_order:
            print(f"\n▶️  Running: {test_name}")
            
            # Check cache first
            if use_cache:
                cached_result = self.result_cache.get(test_name, (), {})
                if cached_result is not None:
                    print(f"  ✅ [CACHED] Result: {cached_result.get('status', 'PASS')}")
                    continue
            
            # Execute test
            start_time = time.perf_counter()
            passed = False
            error = None
            
            try:
                result = test_func()
                passed = True
                print(f"  ✅ PASSED")
            except Exception as e:
                error = str(e)
                print(f"  ❌ FAILED: {error}")
            
            duration = time.perf_counter() - start_time
            
            # Record metrics
            self.metrics.record_test(test_name, duration, passed, error)
            
            # Cache result
            if use_cache:
                self.result_cache.set(test_name, (), {}, {
                    'status': 'PASS' if passed else 'FAIL',
                    'duration': duration,
                    'error': error
                })
            
            print(f"  ⏱️  Duration: {duration:.3f}s")
        
        # Print summary
        self._print_summary()
        
        return self.metrics.get_statistics()
    
    def _print_summary(self):
        """Print test execution summary"""
        print("\n" + "="*80)
        print("TEST EXECUTION SUMMARY")
        print("="*80)
        
        stats = self.metrics.get_statistics()
        cache_stats = self.result_cache.get_stats()
        
        print(f"\n📊 Test Results:")
        print(f"  Total Tests:    {stats['total_tests']}")
        print(f"  Passed:         {stats['passed']} ✅")
        print(f"  Failed:         {stats['failed']} ❌")
        print(f"  Pass Rate:      {stats['pass_rate']}%")
        
        print(f"\n⏱️  Performance:")
        print(f"  Total Time:     {stats['total_execution_time']:.3f}s")
        print(f"  Average Time:   {stats['avg_execution_time']:.3f}s")
        
        print(f"\n🐌 Slowest Tests:")
        for name, duration in stats['slowest_tests']:
            print(f"  {name}: {duration:.3f}s")
        
        print(f"\n💾 Cache Statistics:")
        print(f"  Cache Hits:     {cache_stats['hits']}")
        print(f"  Cache Misses:   {cache_stats['misses']}")
        print(f"  Hit Rate:       {cache_stats['hit_rate']}%")
        print(f"  Cache Size:     {cache_stats['cache_size']} entries")
        
        print("\n" + "="*80)
    
    def list_tests(self) -> Dict[str, dict]:
        """
        List all registered tests with metadata
        Returns dict of test_name -> test_info
        """
        return self.dependency_graph.get_all_tests()
    
    def run_all(self) -> Dict[str, Any]:
        """Run all registered tests"""
        return self.run_tests(filter_prefix=None)
    
    def run_by_category(self, category: str) -> Dict[str, Any]:
        """Run tests in specific category"""
        return self.run_tests()
    
    def run_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """Run tests matching prefix"""
        return self.run_tests(filter_prefix=prefix)
    
    def run_test(self, test_name: str) -> Dict[str, Any]:
        """Run a single test by name"""
        # Find test in dependency graph
        tests = self.dependency_graph.get_all_tests()
        if test_name not in tests:
            print(f"Error: Test '{test_name}' not found")
            return {
                'total_tests': 0,
                'passed': 0,
                'failed': 1,
                'cached': 0,
                'total_time': 0,
                'slowest_tests': [],
                'failed_tests': [(test_name, 'Test not found')]
            }
        
        # Execute single test
        test_func = tests[test_name]['function']
        start_time = time.perf_counter()
        passed = False
        error = None
        
        try:
            result = test_func()
            passed = True
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            error = str(e)
            print(f"❌ {test_name} FAILED: {error}")
        
        duration = time.perf_counter() - start_time
        
        return {
            'total_tests': 1,
            'passed': 1 if passed else 0,
            'failed': 0 if passed else 1,
            'cached': 0,
            'total_time': duration,
            'slowest_tests': [(test_name, duration)],
            'failed_tests': [] if passed else [(test_name, error)]
        }


# Global test runner instance
test_runner = AdvancedTestRunner()


def test(name: str, priority: int = 0, dependencies: List[str] = None, 
         category: str = "general"):
    """
    Decorator to register tests with the advanced framework
    
    Usage:
        @test("test_ocr_extraction", priority=1, category="ocr")
        def my_test():
            assert True
    """
    def decorator(func):
        test_runner.register_test(name, func, priority, dependencies, category)
        return func
    return decorator
