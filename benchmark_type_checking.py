#!/usr/bin/env python3
"""Performance benchmarks for type checking functionality.

This script provides detailed performance benchmarks for the type checking
system in Trellis MCP. It measures execution time, memory usage, and
throughput for various type checking operations.
"""

import time
import tracemalloc
from typing import Any, Dict, List

from trellis_mcp.types import (
    handle_task_by_type,
    is_epic_object,
    is_feature_object,
    is_hierarchy_task,
    is_project_object,
    is_standalone_task,
    is_task_object,
    process_task_generic,
)


def create_test_data(size: int) -> List[Dict[str, Any]]:
    """Create test data for benchmarking."""
    return [
        {
            "kind": "task" if i % 4 == 0 else ["project", "epic", "feature"][i % 3],
            "id": f"T-{i}" if i % 4 == 0 else f"O-{i}",
            "title": f"Test Object {i}",
            "parent": f"F-{i % 10}" if i % 3 == 0 else None,
            "status": "open" if i % 2 == 0 else "done",
            "priority": "high" if i % 5 == 0 else "normal",
        }
        for i in range(size)
    ]


def benchmark_type_guards(test_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Benchmark type guard performance."""
    print("Benchmarking type guard performance...")

    # Benchmark individual type guards
    start_time = time.time()
    task_count = sum(1 for obj in test_data if is_task_object(obj))
    task_guard_time = time.time() - start_time

    start_time = time.time()
    standalone_count = sum(1 for obj in test_data if is_standalone_task(obj))
    standalone_guard_time = time.time() - start_time

    start_time = time.time()
    hierarchy_count = sum(1 for obj in test_data if is_hierarchy_task(obj))
    hierarchy_guard_time = time.time() - start_time

    start_time = time.time()
    project_count = sum(1 for obj in test_data if is_project_object(obj))
    project_guard_time = time.time() - start_time

    start_time = time.time()
    epic_count = sum(1 for obj in test_data if is_epic_object(obj))
    epic_guard_time = time.time() - start_time

    start_time = time.time()
    feature_count = sum(1 for obj in test_data if is_feature_object(obj))
    feature_guard_time = time.time() - start_time

    # Benchmark combined type guard usage
    start_time = time.time()
    categorized_count = 0
    for obj in test_data:
        if is_task_object(obj):
            categorized_count += 1
        elif is_project_object(obj):
            categorized_count += 1
        elif is_epic_object(obj):
            categorized_count += 1
        elif is_feature_object(obj):
            categorized_count += 1
    combined_guard_time = time.time() - start_time

    print(f"  Task objects found: {task_count}")
    print(f"  Standalone tasks: {standalone_count}")
    print(f"  Hierarchy tasks: {hierarchy_count}")
    print(f"  Project objects: {project_count}")
    print(f"  Epic objects: {epic_count}")
    print(f"  Feature objects: {feature_count}")
    print(f"  Total categorized: {categorized_count}")

    return {
        "task_guard": task_guard_time,
        "standalone_guard": standalone_guard_time,
        "hierarchy_guard": hierarchy_guard_time,
        "project_guard": project_guard_time,
        "epic_guard": epic_guard_time,
        "feature_guard": feature_guard_time,
        "combined_guard": combined_guard_time,
    }


def benchmark_generic_functions(test_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Benchmark generic function performance."""
    print("Benchmarking generic function performance...")

    # Filter to only task objects for generic function testing
    task_objects = [obj for obj in test_data if obj.get("kind") == "task"]

    def simple_processor(task):
        task["processed"] = True
        return task

    def standalone_handler(task):
        task["type"] = "standalone"
        return task

    def hierarchy_handler(task):
        task["type"] = "hierarchy"
        return task

    # Benchmark process_task_generic
    start_time = time.time()
    for task in task_objects:
        process_task_generic(task, simple_processor)
    process_generic_time = time.time() - start_time

    # Benchmark handle_task_by_type
    start_time = time.time()
    for task in task_objects:
        handle_task_by_type(task, standalone_handler, hierarchy_handler)
    handle_by_type_time = time.time() - start_time

    print(f"  Task objects processed: {len(task_objects)}")

    return {
        "process_generic": process_generic_time,
        "handle_by_type": handle_by_type_time,
    }


def benchmark_memory_usage(test_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Benchmark memory usage of type checking operations."""
    print("Benchmarking memory usage...")

    # Start memory tracking
    tracemalloc.start()

    # Perform type checking operations
    task_count = 0
    standalone_count = 0
    hierarchy_count = 0

    for obj in test_data:
        if is_task_object(obj):
            task_count += 1
            if is_standalone_task(obj):
                standalone_count += 1
            elif is_hierarchy_task(obj):
                hierarchy_count += 1

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  Current memory usage: {current / 1024 / 1024:.2f} MB")
    print(f"  Peak memory usage: {peak / 1024 / 1024:.2f} MB")

    return {
        "current_memory_mb": current / 1024 / 1024,
        "peak_memory_mb": peak / 1024 / 1024,
    }


def benchmark_scalability(sizes: List[int]) -> Dict[int, Dict[str, float]]:
    """Benchmark scalability with different data sizes."""
    print("Benchmarking scalability...")

    results = {}

    for size in sizes:
        print(f"  Testing with {size} objects...")
        test_data = create_test_data(size)

        # Benchmark type guard performance
        start_time = time.time()
        categorized_count = 0
        for obj in test_data:
            if is_task_object(obj):
                if is_standalone_task(obj):
                    categorized_count += 1
                elif is_hierarchy_task(obj):
                    categorized_count += 1
            elif is_project_object(obj) or is_epic_object(obj) or is_feature_object(obj):
                categorized_count += 1

        execution_time = time.time() - start_time
        throughput = size / execution_time if execution_time > 0 else 0

        results[size] = {
            "execution_time": execution_time,
            "throughput": throughput,
            "categorized_count": categorized_count,
        }

        print(f"    Time: {execution_time:.4f}s, Throughput: {throughput:.0f} obj/s")

    return results


def run_benchmarks():
    """Run all benchmarks and report results."""
    print("Type Checking Performance Benchmarks")
    print("=" * 50)

    # Test data sizes
    test_sizes = [100, 1000, 10000]

    # Create test data
    print(f"Creating test data with {test_sizes[-1]} objects...")
    test_data = create_test_data(test_sizes[-1])

    # Run benchmarks
    print("\n1. Type Guard Performance")
    print("-" * 30)
    type_guard_results = benchmark_type_guards(test_data)

    print("\n2. Generic Function Performance")
    print("-" * 30)
    generic_results = benchmark_generic_functions(test_data)

    print("\n3. Memory Usage")
    print("-" * 30)
    memory_results = benchmark_memory_usage(test_data)

    print("\n4. Scalability")
    print("-" * 30)
    scalability_results = benchmark_scalability(test_sizes)

    # Performance summary
    print("\n" + "=" * 50)
    print("PERFORMANCE SUMMARY")
    print("=" * 50)

    print("\nType Guard Performance (10k objects):")
    for guard_name, time_taken in type_guard_results.items():
        ops_per_second = 10000 / time_taken if time_taken > 0 else 0
        print(f"  {guard_name}: {time_taken:.4f}s ({ops_per_second:.0f} ops/s)")

    print("\nGeneric Function Performance:")
    for func_name, time_taken in generic_results.items():
        task_count = len([obj for obj in test_data if obj.get("kind") == "task"])
        ops_per_second = task_count / time_taken if time_taken > 0 else 0
        print(f"  {func_name}: {time_taken:.4f}s ({ops_per_second:.0f} ops/s)")

    print("\nMemory Usage:")
    print(f"  Current: {memory_results['current_memory_mb']:.2f} MB")
    print(f"  Peak: {memory_results['peak_memory_mb']:.2f} MB")

    print("\nScalability (objects/second):")
    for size, results in scalability_results.items():
        print(f"  {size:5d} objects: {results['throughput']:8.0f} ops/s")

    # Performance thresholds
    print("\n" + "=" * 50)
    print("PERFORMANCE ANALYSIS")
    print("=" * 50)

    # Check if performance meets thresholds
    min_ops_per_second = 10000
    total_type_guard_time = sum(type_guard_results.values())
    avg_ops_per_second = (len(type_guard_results) * 10000) / total_type_guard_time

    print(f"\nAverage type guard performance: {avg_ops_per_second:.0f} ops/s")
    if avg_ops_per_second >= min_ops_per_second:
        print("✅ Performance meets requirements")
    else:
        print("❌ Performance below threshold")

    # Memory usage analysis
    if memory_results["peak_memory_mb"] < 100:
        print("✅ Memory usage is acceptable")
    else:
        print("❌ Memory usage is high")

    # Scalability analysis
    largest_size = max(scalability_results.keys())
    largest_throughput = scalability_results[largest_size]["throughput"]

    if largest_throughput >= 1000:
        print("✅ Scalability is good")
    else:
        print("❌ Scalability needs improvement")

    return {
        "type_guards": type_guard_results,
        "generic_functions": generic_results,
        "memory": memory_results,
        "scalability": scalability_results,
    }


if __name__ == "__main__":
    # Run benchmarks
    results = run_benchmarks()

    # Exit with appropriate code
    print("\nBenchmark completed successfully!")
