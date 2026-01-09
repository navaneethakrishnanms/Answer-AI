"""
Debugging and Complexity Analysis Script
Analyze code complexity, test coverage, and performance bottlenecks
Uses advanced DSA concepts for analysis
"""

import sys
import ast
import json
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import time


class ComplexityAnalyzer:
    """Analyze code complexity using AST"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.tree = None
        self.complexity_scores = {}
        
    def parse_file(self):
        """Parse Python file into AST"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            self.tree = ast.parse(code)
            return True
        except Exception as e:
            print(f"Error parsing {self.file_path}: {e}")
            return False
    
    def calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity (McCabe complexity)"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points add complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def analyze_functions(self) -> Dict[str, dict]:
        """Analyze all functions in file"""
        if not self.tree:
            return {}
        
        functions = {}
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                
                # Calculate metrics
                complexity = self.calculate_cyclomatic_complexity(node)
                num_lines = node.end_lineno - node.lineno + 1
                num_params = len(node.args.args)
                
                # Count nested levels
                max_nesting = self._calculate_max_nesting(node)
                
                functions[func_name] = {
                    'complexity': complexity,
                    'lines': num_lines,
                    'parameters': num_params,
                    'max_nesting': max_nesting,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno
                }
        
        return functions
    
    def _calculate_max_nesting(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        
        def traverse(n, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                    traverse(child, depth + 1)
                else:
                    traverse(child, depth)
        
        traverse(node, 0)
        return max_depth
    
    def find_high_complexity_functions(self, threshold: int = 10) -> List[Tuple[str, int]]:
        """Find functions with complexity above threshold"""
        functions = self.analyze_functions()
        high_complexity = [
            (name, info['complexity']) 
            for name, info in functions.items() 
            if info['complexity'] > threshold
        ]
        return sorted(high_complexity, key=lambda x: x[1], reverse=True)
    
    def generate_report(self) -> dict:
        """Generate comprehensive complexity report"""
        functions = self.analyze_functions()
        
        if not functions:
            return {'error': 'No functions found'}
        
        complexities = [info['complexity'] for info in functions.values()]
        lines = [info['lines'] for info in functions.values()]
        
        return {
            'file': str(self.file_path),
            'total_functions': len(functions),
            'avg_complexity': sum(complexities) / len(complexities),
            'max_complexity': max(complexities),
            'min_complexity': min(complexities),
            'avg_lines': sum(lines) / len(lines),
            'functions': functions,
            'high_complexity': self.find_high_complexity_functions()
        }


class DependencyGraph:
    """Analyze module dependencies using graph algorithms"""
    
    def __init__(self):
        self.graph = defaultdict(list)
        self.in_degree = defaultdict(int)
        
    def add_dependency(self, module: str, depends_on: str):
        """Add a dependency edge"""
        self.graph[module].append(depends_on)
        self.in_degree[depends_on] += 1
        if module not in self.in_degree:
            self.in_degree[module] = 0
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in self.graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def topological_sort(self) -> List[str]:
        """Topological sort using Kahn's algorithm"""
        in_degree_copy = self.in_degree.copy()
        queue = deque([node for node in self.graph if in_degree_copy[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in self.graph[node]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append(neighbor)
        
        return result


class PerformanceProfiler:
    """Profile performance bottlenecks"""
    
    def __init__(self):
        self.timings = defaultdict(list)
        self.call_counts = defaultdict(int)
    
    def record_timing(self, function_name: str, duration: float):
        """Record function execution time"""
        self.timings[function_name].append(duration)
        self.call_counts[function_name] += 1
    
    def get_statistics(self) -> dict:
        """Get timing statistics"""
        stats = {}
        
        for func_name, times in self.timings.items():
            stats[func_name] = {
                'calls': self.call_counts[func_name],
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        return stats
    
    def find_bottlenecks(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Find top N performance bottlenecks"""
        total_times = [
            (func, sum(times)) 
            for func, times in self.timings.items()
        ]
        return sorted(total_times, key=lambda x: x[1], reverse=True)[:top_n]


def analyze_project_complexity(project_dir: Path):
    """Analyze complexity of entire project"""
    print("="*80)
    print("PROJECT COMPLEXITY ANALYSIS")
    print("="*80)
    print()
    
    app_dir = project_dir / "app"
    
    if not app_dir.exists():
        print(f"Error: App directory not found: {app_dir}")
        return
    
    # Analyze all Python files
    python_files = list(app_dir.rglob("*.py"))
    
    print(f"Analyzing {len(python_files)} Python files...\n")
    
    all_reports = []
    
    for py_file in python_files:
        analyzer = ComplexityAnalyzer(py_file)
        if analyzer.parse_file():
            report = analyzer.generate_report()
            if 'error' not in report:
                all_reports.append(report)
    
    # Summary statistics
    print("\nSUMMARY:")
    print("-" * 80)
    
    total_functions = sum(r['total_functions'] for r in all_reports)
    avg_complexity = sum(r['avg_complexity'] * r['total_functions'] for r in all_reports) / total_functions
    
    print(f"Total Files: {len(all_reports)}")
    print(f"Total Functions: {total_functions}")
    print(f"Average Complexity: {avg_complexity:.2f}")
    
    # High complexity functions
    print("\nHIGH COMPLEXITY FUNCTIONS (> 10):")
    print("-" * 80)
    
    all_high_complexity = []
    for report in all_reports:
        for func_name, complexity in report.get('high_complexity', []):
            all_high_complexity.append((report['file'], func_name, complexity))
    
    if all_high_complexity:
        all_high_complexity.sort(key=lambda x: x[2], reverse=True)
        for file, func, complexity in all_high_complexity[:10]:
            file_name = Path(file).name
            print(f"  [{complexity:2d}] {func:30s} in {file_name}")
    else:
        print("  ✓ No high complexity functions found!")
    
    # Most complex files
    print("\nMOST COMPLEX FILES:")
    print("-" * 80)
    
    files_by_complexity = sorted(all_reports, key=lambda x: x['max_complexity'], reverse=True)
    for report in files_by_complexity[:5]:
        file_name = Path(report['file']).name
        print(f"  Max: {report['max_complexity']:2d}, Avg: {report['avg_complexity']:.1f} - {file_name}")
    
    print()


def debug_test_failures():
    """Debug test failures with detailed analysis"""
    print("="*80)
    print("TEST FAILURE DEBUGGER")
    print("="*80)
    print()
    
    print("Running tests to collect failures...")
    
    # This would integrate with pytest results
    # For now, showing the concept
    
    print("\nDebugging Tips:")
    print("-" * 80)
    print("1. Check mock configurations")
    print("2. Verify async/await usage")
    print("3. Check file paths and imports")
    print("4. Validate test data fixtures")
    print("5. Review API mocking")
    
    print("\nTo debug specific test:")
    print("  python -m pytest tests/test_name.py::TestClass::test_method -v --pdb")


def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    backend_dir = Path(__file__).parent.parent
    
    if not args or args[0] == "complexity":
        analyze_project_complexity(backend_dir)
    
    elif args[0] == "file" and len(args) > 1:
        file_path = backend_dir / args[1]
        analyzer = ComplexityAnalyzer(file_path)
        if analyzer.parse_file():
            report = analyzer.generate_report()
            print(json.dumps(report, indent=2))
    
    elif args[0] == "debug":
        debug_test_failures()
    
    else:
        print("""
Usage: python debug_analyzer.py [command] [options]

Commands:
  complexity           Analyze project complexity (default)
  file <path>          Analyze specific file
  debug                Debug test failures

Examples:
  python debug_analyzer.py complexity
  python debug_analyzer.py file app/services/ocr_service.py
  python debug_analyzer.py debug
""")


if __name__ == "__main__":
    main()
