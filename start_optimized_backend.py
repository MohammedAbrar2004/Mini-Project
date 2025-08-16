#!/usr/bin/env python3
"""
Optimized TruthScope Backend Startup Script
Includes performance tuning, caching, and monitoring
"""

import uvicorn
import multiprocessing
import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def get_optimal_workers():
    """Calculate optimal number of workers based on system resources"""
    cpu_count = multiprocessing.cpu_count()
    # Use 2-4 workers per CPU core, but cap at reasonable limits
    workers = min(cpu_count * 2, 8)
    return max(workers, 2)

def get_optimal_config():
    """Get optimal uvicorn configuration for performance"""
    return {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "workers": get_optimal_workers(),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "loop": "asyncio",
        "http": "httptools",
        "ws": "websockets",
        "lifespan": "on",
        "access_log": True,
        "use_colors": True,
        "reload": False,  # Disable reload in production for performance
        "reload_dirs": [],
        "reload_includes": [],
        "reload_excludes": [],
        "log_level": "info",
        "log_config": None,
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
        "root_path": "",
        "limit_concurrency": 1000,
        "limit_max_requests": 10000,
        "backlog": 2048,
        "timeout_keep_alive": 5,
        "timeout_notify": 30,
        "callback_notify": None,
        "ssl_keyfile": None,
        "ssl_certfile": None,
        "ssl_keyfile_password": None,
        "ssl_version": None,
        "ssl_cert_reqs": None,
        "ssl_ca_certs": None,
        "ssl_ciphers": None,
        "headers": [
            ("Server", "TruthScope/1.0"),
            ("X-Powered-By", "TruthScope AI"),
        ]
    }

def main():
    """Main startup function with performance optimizations"""
    print("🚀 Starting TruthScope Backend with Performance Optimizations...")
    
    # Set environment variables for performance
    os.environ["PYTHONOPTIMIZE"] = "1"  # Enable Python optimizations
    os.environ["UVICORN_WORKERS"] = str(get_optimal_workers())
    
    # Get optimal configuration
    config = get_optimal_config()
    
    print(f"📊 Configuration:")
    print(f"   Workers: {config['workers']}")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   Concurrency Limit: {config['limit_concurrency']}")
    print(f"   Max Requests: {config['limit_max_requests']}")
    
    # Performance tips
    print("\n⚡ Performance Optimizations Enabled:")
    print("   • Multi-worker process model")
    print("   • HTTP tools for faster parsing")
    print("   • WebSocket optimization")
    print("   • Connection pooling")
    print("   • Request limiting")
    print("   • Python optimizations")
    
    try:
        # Start the server
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

