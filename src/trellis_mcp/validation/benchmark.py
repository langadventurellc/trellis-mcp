"""Performance benchmarking utilities for validation operations.

This module provides performance measurement tools for cycle detection
and other validation operations.
"""

import logging
import time
from pathlib import Path

# Configure logger for this module
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Utility class for benchmarking cycle detection performance."""

    def __init__(self):
        self.start_time: float | None = None
        self.timings: dict[str, float] = {}

    def start(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Name of the operation being timed
        """
        self.start_time = time.perf_counter()
        logger.debug(f"Starting benchmark: {operation}")

    def end(self, operation: str) -> float:
        """End timing an operation and record the duration.

        Args:
            operation: Name of the operation being timed

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            logger.warning(f"No start time recorded for operation: {operation}")
            return 0.0

        duration = time.perf_counter() - self.start_time
        self.timings[operation] = duration
        logger.debug(f"Completed benchmark: {operation} in {duration:.4f}s")
        self.start_time = None
        return duration

    def get_timings(self) -> dict[str, float]:
        """Get all recorded timings.

        Returns:
            Dictionary mapping operation names to durations in seconds
        """
        return self.timings.copy()

    def log_summary(self) -> None:
        """Log a summary of all benchmarked operations."""
        if not self.timings:
            logger.info("No benchmark timings recorded")
            return

        total_time = sum(self.timings.values())
        logger.info(f"Performance Summary (Total: {total_time:.4f}s):")
        for operation, duration in sorted(self.timings.items()):
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            logger.info(f"  {operation}: {duration:.4f}s ({percentage:.1f}%)")


def benchmark_cycle_detection(project_root: str | Path, operations: int = 10) -> dict[str, float]:
    """Benchmark cycle detection performance.

    This function runs multiple cycle detection operations to measure performance
    characteristics and identify bottlenecks.

    Args:
        project_root: The root directory of the project
        operations: Number of operations to run for averaging

    Returns:
        Dictionary containing benchmark results with operation timings
    """
    # Import here to avoid circular imports
    from .cache import _graph_cache
    from .cycle_detection import check_prereq_cycles

    benchmark = PerformanceBenchmark()
    project_root_path = Path(project_root)

    # Clear cache to get true cold performance
    _graph_cache.clear_cache(project_root_path)

    logger.info(f"Starting cycle detection benchmark with {operations} operations")

    # Run cold (no cache) operation
    benchmark.start("cold_cycle_check")
    try:
        check_prereq_cycles(project_root, benchmark)
    except Exception as e:
        logger.warning(f"Cold cycle check failed: {e}")
    benchmark.end("cold_cycle_check")

    # Run warm (cached) operations
    warm_times = []
    for i in range(operations - 1):  # -1 because we already did cold operation
        warm_benchmark = PerformanceBenchmark()
        warm_benchmark.start(f"warm_cycle_check_{i}")
        try:
            check_prereq_cycles(project_root, warm_benchmark)
        except Exception as e:
            logger.warning(f"Warm cycle check {i} failed: {e}")
        warm_time = warm_benchmark.end(f"warm_cycle_check_{i}")
        warm_times.append(warm_time)

    # Calculate statistics
    results = benchmark.get_timings()
    if warm_times:
        results["avg_warm_time"] = sum(warm_times) / len(warm_times)
        results["min_warm_time"] = min(warm_times)
        results["max_warm_time"] = max(warm_times)

        # Calculate cache effectiveness
        cold_time = results.get("cold_cycle_check", 0)
        avg_warm_time = results["avg_warm_time"]
        if cold_time > 0:
            speedup = cold_time / avg_warm_time if avg_warm_time > 0 else 1
            results["cache_speedup_factor"] = speedup
            results["cache_improvement_percent"] = ((cold_time - avg_warm_time) / cold_time) * 100

    # Log summary
    benchmark.log_summary()
    logger.info(f"Cache performance: {results.get('cache_speedup_factor', 1):.1f}x speedup")

    return results
