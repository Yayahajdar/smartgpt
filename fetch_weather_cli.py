

import os
import sys
import argparse
from weather_data_fetcher import WeatherDataFetcher
import traceback 

def main():
    parser = argparse.ArgumentParser(description='Fetch and visualize historical weather data.')
    parser.add_argument('--ville-id', type=int, required=True, help='ID of the city on historique-meteo.net')
    parser.add_argument('--ville-name', type=str, required=True, help='Name of the city')
    parser.add_argument('--ville-cp', type=str, required=True, help='Postal code of the city')
    parser.add_argument('--year', type=int, required=True, help='Year to fetch data for')
    parser.add_argument('--months', type=int, nargs='+', default=list(range(1, 13)), 
                        help='Months to fetch data for (1-12, defaults to all months)')
    parser.add_argument('--output-dir', type=str, default='visualizations',
                        help='Directory to save visualizations to')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        print(f"Fetching weather data for {args.ville_name} ({args.ville_cp}) for {args.year}...")
        print(f"Months: {', '.join(str(m) for m in args.months)}")
        
        # Create fetcher
        fetcher = WeatherDataFetcher()
        
        # Fetch data
        fetcher.fetch_weather_data(
            ville_id=args.ville_id,
            ville_name=args.ville_name,
            ville_cp=args.ville_cp,
            years=[args.year],
            months=args.months
        )
        
        # Generate visualizations
        print(f"Generating visualizations for {args.ville_name}...")
        df = fetcher.generate_visualizations(args.ville_name, args.output_dir)
        
        print("\nProcessing complete!")
        print(f"Visualizations saved to: {os.path.abspath(args.output_dir)}")
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
