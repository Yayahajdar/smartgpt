#!/usr/bin/env python3


import os
import sys
import glob
from csv_processor import CSVProcessor
import traceback

def main():
    # Check if any arguments were provided
    if len(sys.argv) < 2:
        print("Usage: python process_csv_cli.py [csv_file1] [csv_file2] ... [csv_fileN]")
        print("Example: python process_csv_cli.py uploads/Export_Data_Val*.csv uploads/Export_AIH*.csv")
        return
    
    # Collect all CSV files from the arguments (supporting glob patterns)
    csv_files = []
    for pattern in sys.argv[1:]:
        matched_files = glob.glob(pattern)
        if matched_files:
            csv_files.extend(matched_files)
        else:
            print(f"Warning: No files matched pattern '{pattern}'")
    
    if not csv_files:
        print("Error: No CSV files found with the provided patterns")
        return
    
    print(f"Found {len(csv_files)} CSV files to process:")
    for file in csv_files:
        print(f"  - {file}")
    
    # Create output directory
    output_dir = "visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process the CSV files
    try:
        processor = CSVProcessor(csv_files)
        cleaned_data = processor.process_all(output_dir)
        
        print("\nProcessing complete!")
        print(f"Visualizations saved to: {os.path.abspath(output_dir)}")
        
        # Save cleaned data to new CSV files
        for name, df in cleaned_data.items():
            output_file = f"{output_dir}/{name}_cleaned.csv"
            df.to_csv(output_file, index=False)
            print(f"Cleaned data saved to: {output_file}")
            
    except Exception as e:
        import traceback
        print(f"Error processing CSV files: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
