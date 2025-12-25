#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENCHMARK SCRIPT - Measure parser performance
Uses stdlib only: time + tracemalloc
"""

import sys
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any

# Add tools/ to path
sys.path.insert(0, str(Path(__file__).parent))

from auto_parse import parse_all_indices


def benchmark_parse(input_file: str, output_file: str = '/tmp/benchmark_output.js',
                    runs: int = 3) -> Dict[str, Any]:
    """
    Benchmark parser performance

    Args:
        input_file: Path to input text file
        output_file: Temporary output file
        runs: Number of benchmark runs

    Returns:
        Dictionary with benchmark metrics
    """
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Get file size
    file_size = Path(input_file).stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print(f"📊 BENCHMARK: {input_file}")
    print(f"   File size: {file_size:,} bytes ({file_size_mb:.2f} MB)")
    print(f"   Runs: {runs}")
    print("-" * 60)

    times = []
    mem_peaks = []

    for i in range(runs):
        print(f"Run {i+1}/{runs}...", end=" ")

        # Start memory tracking
        tracemalloc.start()

        # Measure time
        start_time = time.perf_counter()
        success = parse_all_indices(input_file, output_file)
        end_time = time.perf_counter()

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed = end_time - start_time
        times.append(elapsed)
        mem_peaks.append(peak)

        status = "✅" if success else "❌"
        print(f"{status} {elapsed:.3f}s, peak mem: {peak / (1024*1024):.2f} MB")

    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    avg_mem = sum(mem_peaks) / len(mem_peaks)

    print("-" * 60)
    print("📈 RESULTS:")
    print(f"   Average time: {avg_time:.3f}s")
    print(f"   Min time:     {min_time:.3f}s")
    print(f"   Max time:     {max_time:.3f}s")
    print(f"   Avg memory:   {avg_mem / (1024*1024):.2f} MB")
    print(f"   Throughput:   {file_size_mb / avg_time:.2f} MB/s")

    # KPI Check
    print("\n🎯 KPI CHECK:")
    kpi_time_ok = avg_time < 2.0  # Target: < 2s
    kpi_mem_ok = avg_mem < 100 * 1024 * 1024  # Target: < 100 MB increase

    print(f"   Time < 2s:       {'✅ PASS' if kpi_time_ok else '❌ FAIL'} ({avg_time:.3f}s)")
    print(f"   Memory < 100 MB: {'✅ PASS' if kpi_mem_ok else '❌ FAIL'} ({avg_mem / (1024*1024):.2f} MB)")

    all_pass = kpi_time_ok and kpi_mem_ok
    print(f"\n   Overall:        {'✅ ALL KPIs PASS' if all_pass else '❌ SOME KPIs FAIL'}")

    return {
        'file_size_bytes': file_size,
        'file_size_mb': file_size_mb,
        'runs': runs,
        'avg_time_seconds': avg_time,
        'min_time_seconds': min_time,
        'max_time_seconds': max_time,
        'avg_memory_bytes': avg_mem,
        'avg_memory_mb': avg_mem / (1024*1024),
        'throughput_mb_per_sec': file_size_mb / avg_time,
        'kpi_time_pass': kpi_time_ok,
        'kpi_memory_pass': kpi_mem_ok,
        'all_kpi_pass': all_pass
    }


def main():
    """Main entry point"""
    import os

    # Default input file
    project_root = Path(__file__).resolve().parents[1]
    default_input = project_root / "reports" / "txt" / "baocao_full.txt"
    temp_output = "/tmp/benchmark_parser_output.js"

    # Get input from args or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = str(default_input)

    if not os.path.exists(input_file):
        print(f"❌ ERROR: File not found: {input_file}")
        print(f"\nUsage: python benchmark.py [input_file.txt]")
        print(f"\nExample:")
        print(f"   python benchmark.py baocao_full.txt")
        sys.exit(1)

    # Run benchmark
    try:
        results = benchmark_parse(input_file, temp_output, runs=5)

        # Exit with appropriate code
        sys.exit(0 if results['all_kpi_pass'] else 1)

    except Exception as e:
        print(f"\n❌ BENCHMARK ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
