#!/usr/bin/env python3
"""
Script to test the weather data fetching functionality.

Usage:
    python test_fetch.py
"""

from weather_data_fetcher import WeatherDataFetcher
from datetime import datetime, timedelta

def main():
    # Create fetcher
    fetcher = WeatherDataFetcher()
    
    # Set up test parameters
    ville_name = "Roland"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"Testing weather data fetching for {ville_name} from {start_date} to {end_date}")
    print("=" * 70)
    
    # Fetch weather data
    success = fetcher.fetch_weather_data(
        ville_name=ville_name,
        start_date=start_date,
        end_date=end_date
    )
    
    if success:
        print(f"\n✅ Successfully fetched weather data for {ville_name}")
        
        # Process the data
        file_path = f"data/{ville_name}_{start_date}_{end_date}.csv"
        success = fetcher.process_weather_data(ville_name, file_path)
        
        if success:
            print(f"✅ Successfully processed weather data for {ville_name}")
        else:
            print(f"❌ Failed to process weather data for {ville_name}")
    else:
        print(f"\n❌ Failed to fetch weather data for {ville_name}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
