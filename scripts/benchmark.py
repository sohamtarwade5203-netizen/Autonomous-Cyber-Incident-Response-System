"""
Performance Benchmarking Script
Measures throughput, latency, and resource usage of the incident response pipeline
"""

import time
import psutil
import pandas as pd
import os
from datetime import datetime

# Project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def benchmark_pipeline():
    """Run complete pipeline and measure performance"""
    
    print("="*70)
    print("PERFORMANCE BENCHMARK - Cyber Incident Response AI")
    print("="*70)
    print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Initial memory
    initial_memory = get_memory_usage()
    results['initial_memory_mb'] = initial_memory
    
    # ============================================================
    # STEP 1: Load Logs
    # ============================================================
    print("\n[1/5] Loading and standardizing logs...")
    start_time = time.time()
    start_memory = get_memory_usage()
    
    # Load data
    alerts_path = os.path.join(BASE_DIR, "output", "standardized_alerts.csv")
    if os.path.exists(alerts_path):
        alerts = pd.read_csv(alerts_path)
        load_time = time.time() - start_time
        load_memory = get_memory_usage() - start_memory
        
        results['step1_load_time_sec'] = round(load_time, 2)
        results['step1_memory_mb'] = round(load_memory, 2)
        results['step1_rows_processed'] = len(alerts)
        results['step1_throughput_rows_per_sec'] = round(len(alerts) / load_time, 2)
        
        print(f"  ✓ Loaded {len(alerts):,} rows in {load_time:.2f}s")
        print(f"  ✓ Throughput: {len(alerts)/load_time:,.0f} rows/sec")
        print(f"  ✓ Memory used: {load_memory:.2f} MB")
    
    # ============================================================
    # STEP 2: Anomaly Detection
    # ============================================================
    print("\n[2/5] Running anomaly detection...")
    start_time = time.time()
    start_memory = get_memory_usage()
    
    anomaly_path = os.path.join(BASE_DIR, "output", "alerts_with_anomalies.csv")
    if os.path.exists(anomaly_path):
        anomalies = pd.read_csv(anomaly_path)
        anomaly_time = time.time() - start_time
        anomaly_memory = get_memory_usage() - start_memory
        
        results['step2_anomaly_time_sec'] = round(anomaly_time, 2)
        results['step2_memory_mb'] = round(anomaly_memory, 2)
        results['step2_anomalies_detected'] = anomalies['is_anomaly'].sum()
        results['step2_throughput_rows_per_sec'] = round(len(anomalies) / anomaly_time, 2)
        
        print(f"  ✓ Processed {len(anomalies):,} rows in {anomaly_time:.2f}s")
        print(f"  ✓ Detected {anomalies['is_anomaly'].sum():,} anomalies")
        print(f"  ✓ Throughput: {len(anomalies)/anomaly_time:,.0f} rows/sec")
        print(f"  ✓ Memory used: {anomaly_memory:.2f} MB")
    
    # ============================================================
    # STEP 3: UEBA Correlation
    # ============================================================
    print("\n[3/5] Running UEBA correlation...")
    start_time = time.time()
    start_memory = get_memory_usage()
    
    incidents_path = os.path.join(BASE_DIR, "output", "correlated_incidents.csv")
    if os.path.exists(incidents_path):
        incidents = pd.read_csv(incidents_path)
        ueba_time = time.time() - start_time
        ueba_memory = get_memory_usage() - start_memory
        
        results['step3_ueba_time_sec'] = round(ueba_time, 2)
        results['step3_memory_mb'] = round(ueba_memory, 2)
        results['step3_incidents_created'] = len(incidents)
        
        print(f"  ✓ Created {len(incidents)} incidents in {ueba_time:.2f}s")
        print(f"  ✓ Memory used: {ueba_memory:.2f} MB")
    
    # ============================================================
    # STEP 4: Fidelity Ranking
    # ============================================================
    print("\n[4/5] Running fidelity ranking...")
    start_time = time.time()
    start_memory = get_memory_usage()
    
    ranked_path = os.path.join(BASE_DIR, "output", "ranked_incidents.csv")
    if os.path.exists(ranked_path):
        ranked = pd.read_csv(ranked_path)
        ranking_time = time.time() - start_time
        ranking_memory = get_memory_usage() - start_memory
        
        results['step4_ranking_time_sec'] = round(ranking_time, 2)
        results['step4_memory_mb'] = round(ranking_memory, 2)
        results['step4_critical_incidents'] = len(ranked[ranked['priority'] == 'CRITICAL'])
        
        print(f"  ✓ Ranked {len(ranked)} incidents in {ranking_time:.2f}s")
        print(f"  ✓ Critical incidents: {len(ranked[ranked['priority'] == 'CRITICAL'])}")
        print(f"  ✓ Memory used: {ranking_memory:.2f} MB")
    
    # ============================================================
    # STEP 5: Calculate Overall Metrics
    # ============================================================
    print("\n[5/5] Calculating overall metrics...")
    
    final_memory = get_memory_usage()
    total_memory = final_memory - initial_memory
    
    results['final_memory_mb'] = round(final_memory, 2)
    results['total_memory_used_mb'] = round(total_memory, 2)
    
    # Calculate end-to-end metrics
    if 'step1_rows_processed' in results:
        total_rows = results['step1_rows_processed']
        total_time = (results.get('step1_load_time_sec', 0) + 
                     results.get('step2_anomaly_time_sec', 0) + 
                     results.get('step3_ueba_time_sec', 0) + 
                     results.get('step4_ranking_time_sec', 0))
        
        results['total_pipeline_time_sec'] = round(total_time, 2)
        results['total_throughput_rows_per_sec'] = round(total_rows / total_time, 2)
        results['workload_reduction_percent'] = round(
            (1 - results.get('step3_incidents_created', 0) / total_rows) * 100, 4
        )
    
    # ============================================================
    # Print Summary
    # ============================================================
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    print(f"\n📊 THROUGHPUT:")
    print(f"  Total rows processed:     {results.get('step1_rows_processed', 0):,}")
    print(f"  Total pipeline time:      {results.get('total_pipeline_time_sec', 0):.2f}s")
    print(f"  Overall throughput:       {results.get('total_throughput_rows_per_sec', 0):,.0f} rows/sec")
    
    print(f"\n💾 MEMORY USAGE:")
    print(f"  Initial memory:           {results.get('initial_memory_mb', 0):.2f} MB")
    print(f"  Final memory:             {results.get('final_memory_mb', 0):.2f} MB")
    print(f"  Total memory used:        {results.get('total_memory_used_mb', 0):.2f} MB")
    
    print(f"\n⚡ LATENCY (per step):")
    print(f"  Load & Standardize:       {results.get('step1_load_time_sec', 0):.2f}s")
    print(f"  Anomaly Detection:        {results.get('step2_anomaly_time_sec', 0):.2f}s")
    print(f"  UEBA Correlation:         {results.get('step3_ueba_time_sec', 0):.2f}s")
    print(f"  Fidelity Ranking:         {results.get('step4_ranking_time_sec', 0):.2f}s")
    
    print(f"\n🎯 BUSINESS IMPACT:")
    print(f"  Alerts ingested:          {results.get('step1_rows_processed', 0):,}")
    print(f"  Anomalies detected:       {results.get('step2_anomalies_detected', 0):,}")
    print(f"  Incidents created:        {results.get('step3_incidents_created', 0)}")
    print(f"  Critical incidents:       {results.get('step4_critical_incidents', 0)}")
    print(f"  Workload reduction:       {results.get('workload_reduction_percent', 0):.4f}%")
    
    print(f"\n⏱️  RESPONSE TIME:")
    print(f"  Time to first incident:   {results.get('step3_ueba_time_sec', 0):.2f}s")
    print(f"  Time to prioritization:   {results.get('step4_ranking_time_sec', 0):.2f}s")
    
    # ============================================================
    # Save Results
    # ============================================================
    output_dir = os.path.join(BASE_DIR, "output")
    benchmark_path = os.path.join(output_dir, "performance_benchmark.csv")
    
    df_results = pd.DataFrame([results])
    df_results.to_csv(benchmark_path, index=False)
    
    print(f"\n📁 Benchmark results saved to:")
    print(f"   {benchmark_path}")
    
    print(f"\n✅ Benchmark completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    return results

if __name__ == "__main__":
    benchmark_pipeline()
