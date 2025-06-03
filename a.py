import os
from dotenv import load_dotenv
import requests

load_dotenv()

apis = {
    "ClimateTrace": os.getenv("CLIMATETRACE_API_BASE"),
    "CarbonInterface": os.getenv("CARBON_INTERFACE_API_BASE"),
    "NASA": os.getenv("NASA_API_BASE"),
    "OpenWeather": os.getenv("OPENWEATHER_API_BASE"),
    "UN_SDG": os.getenv("UN_SDG_API_BASE"),
    "WorldBank": os.getenv("WORLD_BANK_API_BASE"),
    "WatsonX": os.getenv("IBM_CLOUD_URL"),
}

for name, url in apis.items():
    print(f"\nTesting {name} -> {url}")
    try:
        r = requests.get(url, timeout=5)
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

