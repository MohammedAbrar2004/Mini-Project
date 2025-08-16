#!/usr/bin/env python3
"""
Performance Monitor for TruthScope
Monitors API response times, cache hit rates, and system performance
"""

import time
import requests
import psutil
import json
from datetime import datetime
from typing import Dict, List, Optional
import threading
import statistics

class PerformanceMonitor:
    """Monitors TruthScope system performance"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.metrics = {
            "api_calls": [],
            "response_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": [],
            "system_stats": []
        }
        self.running = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: int = 30):
        """Start continuous monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"🔍 Performance monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("🛑 Performance monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.running:
            try:
                self._collect_system_stats()
                self._test_api_endpoints()
                time.sleep(interval)
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
    
    def _collect_system_stats(self):
        """Collect system performance statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available / (1024**3),  # GB
                "disk_percent": disk.percent,
                "disk_free": disk.free / (1024**3)  # GB
            }
            
            self.metrics["system_stats"].append(stats)
            
            # Keep only last 100 entries
            if len(self.metrics["system_stats"]) > 100:
                self.metrics["system_stats"] = self.metrics["system_stats"][-100:]
                
        except Exception as e:
            print(f"❌ Error collecting system stats: {e}")
    
    def _test_api_endpoints(self):
        """Test API endpoints and measure response times"""
        endpoints = [
            "/health",
            "/cache/status",
            "/api/fact-check"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                
                if endpoint == "/api/fact-check":
                    # Test with a sample claim
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json={"text": "Sample claim for performance testing"},
                        timeout=10
                    )
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                response_time = time.time() - start_time
                
                # Record metrics
                self.metrics["api_calls"].append({
                    "endpoint": endpoint,
                    "timestamp": datetime.now().isoformat(),
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "success": response.status_code < 400
                })
                
                # Check if response was cached
                if "cached" in response.headers or "cached" in response.text.lower():
                    self.metrics["cache_hits"] += 1
                else:
                    self.metrics["cache_misses"] += 1
                
                # Keep only last 1000 API calls
                if len(self.metrics["api_calls"]) > 1000:
                    self.metrics["api_calls"] = self.metrics["api_calls"][-1000:]
                
            except Exception as e:
                self.metrics["errors"].append({
                    "endpoint": endpoint,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })
                
                # Keep only last 100 errors
                if len(self.metrics["errors"]) > 100:
                    self.metrics["errors"] = self.metrics["errors"][-100:]
    
    def get_performance_summary(self) -> Dict:
        """Get a summary of current performance metrics"""
        if not self.metrics["api_calls"]:
            return {"status": "No data collected yet"}
        
        # Calculate response time statistics
        response_times = [call["response_time"] for call in self.metrics["api_calls"]]
        
        # Calculate cache hit rate
        total_cache_operations = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_cache_operations * 100) if total_cache_operations > 0 else 0
        
        # Calculate success rate
        successful_calls = sum(1 for call in self.metrics["api_calls"] if call["success"])
        success_rate = (successful_calls / len(self.metrics["api_calls"])) * 100
        
        # Get latest system stats
        latest_system_stats = self.metrics["system_stats"][-1] if self.metrics["system_stats"] else {}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_api_calls": len(self.metrics["api_calls"]),
            "response_time_stats": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            },
            "cache_performance": {
                "hits": self.metrics["cache_hits"],
                "misses": self.metrics["cache_misses"],
                "hit_rate": round(cache_hit_rate, 2)
            },
            "success_rate": round(success_rate, 2),
            "error_count": len(self.metrics["errors"]),
            "system_performance": latest_system_stats
        }
    
    def print_performance_report(self):
        """Print a formatted performance report"""
        summary = self.get_performance_summary()
        
        if summary.get("status") == "No data collected yet":
            print("📊 No performance data available yet. Start monitoring first.")
            return
        
        print("\n" + "="*60)
        print("📊 TRUTHSCOPE PERFORMANCE REPORT")
        print("="*60)
        print(f"📅 Generated: {summary['timestamp']}")
        print(f"📈 Total API Calls: {summary['total_api_calls']}")
        
        # Response time stats
        rt = summary['response_time_stats']
        print(f"\n⏱️  Response Time Statistics:")
        print(f"   Min: {rt['min']:.3f}s")
        print(f"   Max: {rt['max']:.3f}s")
        print(f"   Mean: {rt['mean']:.3f}s")
        print(f"   Median: {rt['median']:.3f}s")
        print(f"   95th Percentile: {rt['p95']:.3f}s")
        
        # Cache performance
        cache = summary['cache_performance']
        print(f"\n💾 Cache Performance:")
        print(f"   Hits: {cache['hits']}")
        print(f"   Misses: {cache['misses']}")
        print(f"   Hit Rate: {cache['hit_rate']}%")
        
        # Success rate
        print(f"\n✅ Success Rate: {summary['success_rate']}%")
        print(f"❌ Errors: {summary['error_count']}")
        
        # System performance
        if summary['system_performance']:
            sys = summary['system_performance']
            print(f"\n🖥️  System Performance:")
            print(f"   CPU Usage: {sys.get('cpu_percent', 'N/A')}%")
            print(f"   Memory Usage: {sys.get('memory_percent', 'N/A')}%")
            print(f"   Available Memory: {sys.get('memory_available', 'N/A'):.2f} GB")
            print(f"   Disk Usage: {sys.get('disk_percent', 'N/A')}%")
        
        print("="*60)
    
    def export_metrics(self, filename: str = "performance_metrics.json"):
        """Export metrics to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            print(f"📁 Metrics exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting metrics: {e}")

def main():
    """Main function for standalone monitoring"""
    monitor = PerformanceMonitor()
    
    try:
        print("🚀 TruthScope Performance Monitor")
        print("Press Ctrl+C to stop monitoring and view report")
        
        # Start monitoring
        monitor.start_monitoring(interval=15)  # Check every 15 seconds
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        
        # Generate and display report
        monitor.print_performance_report()
        
        # Export metrics
        monitor.export_metrics()
        
        # Stop monitoring
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()

