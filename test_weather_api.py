#!/usr/bin/env python3
"""
Script to test if the Visual Crossing Weather API key in the .env file is valid.

Usage:
    python test_weather_api.py
"""

import os
import requests
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from .env
    api_key = os.getenv('WEATHER_API_KEY')
    
    if not api_key or api_key == 'your_api_key_here':
        print("❌ API key not set or using default value.")
        print("Please update the WEATHER_API_KEY value in your .env file.")
        return False
    
    print(f"Testing API key: {api_key[:5]}...")
    
    # Test URL - get weather for Paris for a single day
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Paris,France/2023-01-01/2023-01-01?unitGroup=metric&include=days&key={api_key}&contentType=json"
    
    try:
        # Make a test request
        response = requests.get(url)
        
        # Check the response
        if response.status_code == 200:
            data = response.json()
            if 'days' in data and len(data['days']) > 0:
                day = data['days'][0]
                print("✅ API key is valid!")
                print(f"Test data for Paris on 2023-01-01:")
                print(f"  Temperature: {day.get('temp')}°C")
                print(f"  Min Temperature: {day.get('tempmin')}°C")
                print(f"  Max Temperature: {day.get('tempmax')}°C")
                print(f"  Humidity: {day.get('humidity')}%")
                print(f"  Conditions: {day.get('conditions')}")
                print("\nYou can now use the historical weather data feature.")
                return True
            else:
                print("❌ API response doesn't contain expected data.")
                print("Please check your API key.")
                return False
        elif response.status_code == 401 or response.status_code == 403:
            print(f"❌ API key is invalid (Status code: {response.status_code}).")
            print("Please update the WEATHER_API_KEY value in your .env file.")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            print("Please check your API key and internet connection.")
            return False
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

if __name__ == "__main__":
    main()
