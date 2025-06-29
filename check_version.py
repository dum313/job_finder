#!/usr/bin/env python3
import sys
import platform

print("=== Python Version ===")
print(f"Version: {sys.version}")
print(f"Version Info: {sys.version_info}")
print(f"Platform: {platform.platform()}")
print(f"Executable: {sys.executable}")
print("\n=== Environment Variables ===")
print(f"PATH: {sys.path}")
print(f"PYTHONPATH: {sys.path}")

# Check important packages
try:
    import aiohttp
    print("\n=== aiohttp ===")
    print(f"Version: {aiohttp.__version__}")
except ImportError as e:
    print(f"\n=== aiohub not installed: {e}")

try:
    import requests
    print("\n=== requests ===")
    print(f"Version: {requests.__version__}")
except ImportError as e:
    print(f"\n=== requests not installed: {e}")
