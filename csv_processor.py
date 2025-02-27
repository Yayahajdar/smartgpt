#!/usr/bin/env python3
"""
CSV Data Processor and Visualizer

This script imports multiple CSV files, cleans the data, and creates visualizations.
"""

import os
import pandas as pd
import numpy as np
# Set matplotlib backend to non-GUI backend to avoid macOS issues
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from datetime import datetime

# Set style for matplotlib
plt.style.use('ggplot')
sns.set(style="whitegrid")

class CSVProcessor:
    def __init__(self, file_paths):
        """Initialize with a list of CSV file paths."""
        self.file_paths = file_paths
        self.dataframes = {}
        self.cleaned_dataframes = {}
        
    def import_csv_files(self):
        """Import all CSV files."""
        for file_path in self.file_paths:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
                
            try:
                # Get the file name without extension
                file_name = os.path.basename(file_path).split('.')[0]
                
                # Detect the delimiter (assuming it's either comma or semicolon)
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    delimiter = ';' if ';' in first_line else ','
                
                # Read the CSV file
                df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8')
                
                # Store the dataframe
                self.dataframes[file_name] = df
                print(f"Successfully imported: {file_name}")
                print(f"Shape: {df.shape}")
                print(f"Columns: {df.columns.tolist()}")
                print("-" * 50)
            except Exception as e:
                print(f"Error importing {file_path}: {str(e)}")
    
    def clean_data(self):
        """Clean all imported dataframes."""
        for name, df in self.dataframes.items():
            try:
                # Create a copy to avoid modifying the original
                cleaned_df = df.copy()
                
                # Convert date columns to datetime
                date_columns = [col for col in cleaned_df.columns if 'date' in col.lower() or 'time' in col.lower()]
                for col in date_columns:
                    try:
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
                    except:
                        print(f"Could not convert {col} to datetime in {name}")
                
                # If there's a column named 'Date' but not detected above
                if 'Date' in cleaned_df.columns and 'Date' not in date_columns:
                    try:
                        cleaned_df['Date'] = pd.to_datetime(cleaned_df['Date'], errors='coerce')
                    except:
                        print(f"Could not convert Date to datetime in {name}")
                
                # Handle numeric values with comma as decimal separator
                numeric_columns = cleaned_df.select_dtypes(include=['object']).columns
                for col in numeric_columns:
                    # Check if column contains numeric values with comma as decimal separator
                    if cleaned_df[col].str.contains(',', regex=False).any():
                        try:
                            # Replace comma with dot and convert to float
                            cleaned_df[col] = cleaned_df[col].str.replace(',', '.').astype(float)
                        except:
                            print(f"Could not convert {col} with comma to float in {name}")
                
                # Drop rows with all NaN values
                cleaned_df = cleaned_df.dropna(how='all')
                
                # Store the cleaned dataframe
                self.cleaned_dataframes[name] = cleaned_df
                print(f"Successfully cleaned: {name}")
                print(f"Original shape: {df.shape}, Cleaned shape: {cleaned_df.shape}")
                print("-" * 50)
            except Exception as e:
                print(f"Error cleaning {name}: {str(e)}")
    
    def generate_summary_statistics(self):
        """Generate summary statistics for all cleaned dataframes."""
        for name, df in self.cleaned_dataframes.items():
            try:
                print(f"Summary statistics for {name}:")
                
                # Get numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                if numeric_cols:
                    # Calculate statistics for numeric columns
                    stats = df[numeric_cols].describe()
                    print(stats)
                else:
                    print("No numeric columns found.")
                
                print("-" * 50)
            except Exception as e:
                print(f"Error generating statistics for {name}: {str(e)}")
    
    def visualize_data(self, output_dir="visualizations"):
        """Create visualizations for the cleaned data."""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        for name, df in self.cleaned_dataframes.items():
            try:
                print(f"Creating visualizations for {name}...")
                
                # Identify date columns and numeric columns
                date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                # If we have date and numeric columns, create time series plots
                if date_cols and numeric_cols:
                    for date_col in date_cols:
                        for numeric_col in numeric_cols[:5]:  # Limit to first 5 numeric columns to avoid too many plots
                            try:
                                # Create a time series plot using matplotlib
                                plt.figure(figsize=(12, 6))
                                plt.plot(df[date_col], df[numeric_col])
                                plt.title(f'{numeric_col} over time')
                                plt.xlabel(date_col)
                                plt.ylabel(numeric_col)
                                plt.xticks(rotation=45)
                                plt.tight_layout()
                                plt.savefig(f"{output_dir}/{name}_{numeric_col}_timeseries.png")
                                plt.close()
                                
                                # Create an interactive time series plot using plotly
                                fig = px.line(df, x=date_col, y=numeric_col, 
                                             title=f'{numeric_col} over time')
                                fig.update_layout(xaxis_title=date_col, yaxis_title=numeric_col)
                                fig.write_html(f"{output_dir}/{name}_{numeric_col}_timeseries.html")
                            except Exception as e:
                                print(f"Error creating time series plot for {numeric_col}: {str(e)}")
                
                # Create distribution plots for numeric columns
                for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                    try:
                        # Create a histogram using matplotlib
                        plt.figure(figsize=(10, 6))
                        sns.histplot(df[col].dropna(), kde=True)
                        plt.title(f'Distribution of {col}')
                        plt.xlabel(col)
                        plt.ylabel('Frequency')
                        plt.tight_layout()
                        plt.savefig(f"{output_dir}/{name}_{col}_distribution.png")
                        plt.close()
                        
                        # Create an interactive histogram using plotly
                        fig = px.histogram(df, x=col, marginal="box", 
                                          title=f'Distribution of {col}')
                        fig.update_layout(xaxis_title=col, yaxis_title='Frequency')
                        fig.write_html(f"{output_dir}/{name}_{col}_distribution.html")
                    except Exception as e:
                        print(f"Error creating distribution plot for {col}: {str(e)}")
                
                # Create correlation heatmap if there are multiple numeric columns
                if len(numeric_cols) > 1:
                    try:
                        # Calculate correlation matrix
                        corr_matrix = df[numeric_cols].corr()
                        
                        # Create a heatmap using seaborn
                        plt.figure(figsize=(12, 10))
                        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
                        plt.title(f'Correlation Matrix for {name}')
                        plt.tight_layout()
                        plt.savefig(f"{output_dir}/{name}_correlation_heatmap.png")
                        plt.close()
                        
                        # Create an interactive heatmap using plotly
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns,
                            y=corr_matrix.index,
                            colorscale='RdBu_r',
                            zmin=-1, zmax=1,
                            text=corr_matrix.round(2).values,
                            texttemplate="%{text}",
                            textfont={"size":10}
                        ))
                        fig.update_layout(title=f'Correlation Matrix for {name}')
                        fig.write_html(f"{output_dir}/{name}_correlation_heatmap.html")
                    except Exception as e:
                        print(f"Error creating correlation heatmap: {str(e)}")
                
                print(f"Visualizations for {name} saved to {output_dir}")
                print("-" * 50)
            except Exception as e:
                print(f"Error visualizing {name}: {str(e)}")
    
    def process_all(self, output_dir="visualizations"):
        """Run the complete processing pipeline."""
        self.import_csv_files()
        self.clean_data()
        self.generate_summary_statistics()
        self.visualize_data(output_dir)
        
        return self.cleaned_dataframes


def main():
    # Define the CSV file paths
    csv_files = [
        "/Users/daryahya/Documents/smartgpt/uploads/Export_Data_Val de Roland_2024-05-09_15h49.csv",
        "/Users/daryahya/Documents/smartgpt/uploads/Export_AIH_2024-10-10_12h08.csv"
    ]
    
    # Create output directory
    output_dir = "/Users/daryahya/Documents/smartgpt/visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process the CSV files
    processor = CSVProcessor(csv_files)
    cleaned_data = processor.process_all(output_dir)
    
    print("\nProcessing complete!")
    print(f"Visualizations saved to: {output_dir}")
    
    # Save cleaned data to new CSV files
    for name, df in cleaned_data.items():
        output_file = f"{output_dir}/{name}_cleaned.csv"
        df.to_csv(output_file, index=False)
        print(f"Cleaned data saved to: {output_file}")


if __name__ == "__main__":
    main()
