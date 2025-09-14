import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EXCHANGERATE_API_KEY")
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"

def get_conversion_rates():
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return data.get("conversion_rates", {"USD": 1.0})
    except requests.RequestException as e:
        print(f"Could not fetch currency rates: {e}")
    return {"USD": 1.0} # Fallback