"""
RingTrace: Main Application Launcher & Network Server
Starts the FastAPI application and Analyst Workspace on 0.0.0.0 so that
ANY device (local PC, mobile phone, other laptops on Wi-Fi, or judges) can access it.
"""

import sys
import os
import socket
import uvicorn

# Ensure the root directory is on the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def get_local_ip() -> str:
    """Attempts to find the primary IPv4 address on the local network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "10.221.9.185"


def main():
    port = int(os.environ.get("PORT", 8080))
    local_ip = get_local_ip()

    banner = rf"""
  ========================================================================
   ____  _             _____                    
  |  _ \(_)_ __   __ _|_   _| __ __ _  ___ ___  
  | |_) | | '_ \ / _` | | || '__/ _` |/ __/ _ \ 
  |  _ <| | | | | (_| | | || | | (_| | (_|  __/ 
  |_| \_\_|_| |_|\__, | |_||_|  \__,_|\___\___| 
                 |___/                          
  ========================================================================
  Evidence-Grounded Financial Crime Investigation
  with Adversarial Case Stress-Testing
  ------------------------------------------------------------------------
  * Team: Twilight (Saveetha Engineering College)
  * Track: Agentic AI / FinTech (K! Hacks 4.0)
  
  [ACCESSIBLE ON ANY DEVICE / ANY SYSTEM]:
  -> On This Laptop:         http://localhost:{port}
  -> On Any Mobile / Wi-Fi:  http://{local_ip}:{port}
  -> Interactive API Docs:   http://{local_ip}:{port}/docs
  ========================================================================
    """
    print(banner)
    print(f">> Server running on 0.0.0.0:{port}")
    print(f">> Open on your phone / other laptops: http://{local_ip}:{port}")
    print(">> Press Ctrl+C to terminate.\n")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
