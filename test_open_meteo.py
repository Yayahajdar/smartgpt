#!/usr/bin/env python3
"""
Script to test the Open-Meteo API for Roland and Tours in France.

Usage:
    python test_open_meteo.py
"""

import requests
import json
from datetime import datetime, timedelta

def main():
    # Cities to test
    cities = {
        'Roland': {'latitude': 47.3900, 'longitude': 0.6900},
        'Tours': {'latitude': 47.3941, 'longitude': 0.6848}
    }
    
    # Date range (last 7 days)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"Testing Open-Meteo API for Roland and Tours from {start_date} to {end_date}")
    print("=" * 70)
    
    for city_name, coords in cities.items():
        print(f"\nTesting {city_name}:")
        
        # Construct API URL
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={coords['latitude']}&longitude={coords['longitude']}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant&timezone=Europe%2FBerlin"
        
        try:
            # Make API request
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'daily' in data:
                    daily = data['daily']
                    dates = daily.get('time', [])
                    temp_max = daily.get('temperature_2m_max', [])
                    temp_min = daily.get('temperature_2m_min', [])
                    
                    print(f"✅ API returned data successfully for {city_name}")
                    print(f"  Data points: {len(dates)}")
                    
                    # Print sample data
                    print("\n  Sample data:")
                    print("  " + "-" * 50)
                    print("  Date       | Min Temp | Max Temp")
                    print("  " + "-" * 50)
                    
                    for i in range(min(3, len(dates))):
                        print(f"  {dates[i]} | {temp_min[i]:7.1f}°C | {temp_max[i]:7.1f}°C")
                    
                    print("  " + "-" * 50)
                else:
                    print(f"❌ No daily data found for {city_name}")
            else:
                print(f"❌ API request failed with status code {response.status_code}")
                print(f"  Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Error testing API for {city_name}: {e}")
    
    print("\n" + "=" * 70)
    print("Test completed!")

if __name__ == "__main__":
    main()
