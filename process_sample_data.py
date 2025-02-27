

import os
from dotenv import load_dotenv
from weather_data_fetcher import WeatherDataFetcher

def main():
    # Load environment variables
    load_dotenv()
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create visualizations directory if it doesn't exist
    viz_dir = 'static/visualizations'
    os.makedirs(viz_dir, exist_ok=True)
    
    # Sample data file
    sample_file = 'data/sample_weather_data.csv'
    
    # Check if the sample file exists
    if not os.path.exists(sample_file):
        print(f"❌ Sample data file not found: {sample_file}")
        return False
    
    try:
        # Create weather data fetcher
        fetcher = WeatherDataFetcher()
        
        # Process the sample data
        print(f"Processing sample data file: {sample_file}")
        ville_name = "SampleCity"
        
        # Process the data
        success = fetcher.process_weather_data(ville_name, sample_file)
        
        if not success:
            print("❌ Failed to process sample data.")
            return False
        
        # Generate visualizations
        print(f"Generating visualizations for {ville_name}")
        df = fetcher.generate_visualizations(ville_name, viz_dir)
        
        if df.empty:
            print("❌ No data was processed.")
            return False
        
        # List generated visualization files
        print("\n✅ Visualizations generated:")
        for root, _, files in os.walk(viz_dir):
            for file in files:
                if file.startswith(f"{ville_name}_"):
                    print(f"  - {os.path.join(root, file)}")
        
        print("\n✅ Sample data processed successfully!")
        return True
    
    except Exception as e:
        import traceback
        print(f"❌ Error processing sample data: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()
