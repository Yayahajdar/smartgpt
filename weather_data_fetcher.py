#!/usr/bin/env python3
"""
Weather Data Fetcher

This script fetches historical weather data from Open-Meteo API and stores it in a SQLite database.
It also generates hourly temperature data using min/max temperatures with a sine function.
"""

import requests
import dotenv
import os
import csv
import sqlite3
import math
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.dates as mdates
import traceback

class WeatherDataFetcher:
    def __init__(self, db_path=None):
        """Initialize the weather data fetcher."""
        # Load environment variables
        dotenv.load_dotenv()
        
        # Set up database connection
        self.db_path = db_path or os.getenv('SQLITE_DB')
        if not self.db_path:
            raise ValueError("Database path not provided and SQLITE_DB environment variable not set")
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize the database
        self.initialize_db()
        
    def initialize_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Mesures table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Mesures (
            BAT TEXT,
            Datetime TEXT,
            Objet TEXT,
            Commande TEXT,
            Name TEXT,
            Type TEXT,
            Value REAL,
            Unit TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized at {self.db_path}")
        
    def connect_db(self):
        """Connect to the SQLite database."""
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        
        return conn
    
    def store_weather_data(self, processed_df):
        """Store processed weather data in the database."""
        import sqlite3
        import traceback
        
        try:
            # Connect to database
            conn = sqlite3.connect('smarthome.db')
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    BAT TEXT,
                    Datetime TEXT,
                    Objet TEXT,
                    Commande TEXT,
                    Name TEXT,
                    Type TEXT,
                    Value REAL,
                    Unit TEXT,
                    Timestamp INTEGER
                )
            ''')
            
            # Insert data
            for _, item in processed_df.iterrows():
                cursor.execute('''
                    INSERT INTO history (BAT, Datetime, Objet, Commande, Name, Type, Value, Unit, Timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', 
                    (
                        item['BAT'],
                        item['Datetime'],
                        item.get('Objet', ''),
                        item.get('Commande', ''),
                        item.get('Name', ''),
                        item.get('Type', ''),
                        item['Value'],
                        item.get('Unit', '°C'),  # Set default unit to '°C'
                        0
                    )
                )
            
            # Commit changes
            conn.commit()
            
            print(f"Stored {len(processed_df)} weather data points in database")
            return True
            
        except Exception as e:
            print(f"Error storing weather data: {e}")
            print(traceback.format_exc())
            return False
            
        finally:
            # Close connection
            if 'conn' in locals():
                conn.close()
        
    def fetch_weather_data(self, ville_name, start_date, end_date):
        """Fetch weather data for a given city and date range using Open-Meteo free API."""
        import requests
        import os
        from datetime import datetime, timedelta
        import time
        import random
        import traceback
        
        print(f"Starting fetch for {ville_name} from {start_date} to {end_date}")
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Format dates
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            print(f"Error parsing dates: {e}")
            return False
        
        # Check if date range is valid
        if start_date_obj > end_date_obj:
            print(f"Error: Start date {start_date} is after end date {end_date}")
            return False
        
        # Calculate number of days
        delta = end_date_obj - start_date_obj
        num_days = delta.days + 1
        
        if num_days > 365:
            print(f"Error: Date range too large ({num_days} days). Maximum is 365 days.")
            return False
        
        # Map French city names to coordinates (latitude, longitude)
        city_coordinates = {
            'Paris': {'latitude': 48.8566, 'longitude': 2.3522},
            'Marseille': {'latitude': 43.2965, 'longitude': 5.3698},
            'Lyon': {'latitude': 45.7578, 'longitude': 4.8320},
            'Toulouse': {'latitude': 43.6047, 'longitude': 1.4442},
            'Nice': {'latitude': 43.7102, 'longitude': 7.2620},
            'Nantes': {'latitude': 47.2184, 'longitude': -1.5536},
            'Strasbourg': {'latitude': 48.5734, 'longitude': 7.7521},
            'Montpellier': {'latitude': 43.6108, 'longitude': 3.8767},
            'Bordeaux': {'latitude': 44.8378, 'longitude': -0.5792},
            'Lille': {'latitude': 50.6292, 'longitude': 3.0573},
            'Tours': {'latitude': 47.3941, 'longitude': 0.6848},
            'Roland': {'latitude': 47.3900, 'longitude': 0.6900},  # Approximate coordinates near Tours
            'SampleCity': {'latitude': 48.8566, 'longitude': 2.3522}  # Use Paris for sample
        }
        
        # Check if we have coordinates for this city
        if ville_name not in city_coordinates:
            print(f"Error: No coordinates found for '{ville_name}'")
            return False
        
        # Get coordinates
        latitude = city_coordinates[ville_name]['latitude']
        longitude = city_coordinates[ville_name]['longitude']
        
        # Use Open-Meteo API (free, no API key required)
        base_url = "https://archive-api.open-meteo.com/v1/archive"
        
        # Construct API URL
        url = f"{base_url}?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant&timezone=Europe%2FBerlin"
        
        print(f"Fetching weather data for {ville_name} from {start_date} to {end_date}")
        print(f"API URL: {url}")
        
        try:
            # Make API request
            response = requests.get(url)
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error fetching data: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            # Parse JSON response
            data = response.json()
            
            # Convert to CSV format
            csv_data = "date,temp_max,temp_min,temp_mean,precipitation,windspeed,winddirection\n"
            
            # Check if we have daily data
            if 'daily' not in data:
                print("Error: No daily data in response")
                print(f"Response: {data}")
                return False
            
            # Get daily data
            daily = data['daily']
            dates = daily.get('time', [])
            temp_max = daily.get('temperature_2m_max', [])
            temp_min = daily.get('temperature_2m_min', [])
            temp_mean = daily.get('temperature_2m_mean', [])
            precip = daily.get('precipitation_sum', [])
            windspeed = daily.get('windspeed_10m_max', [])
            winddir = daily.get('winddirection_10m_dominant', [])
            
            print(f"Retrieved {len(dates)} days of weather data")
            
            # Create CSV rows
            for i in range(len(dates)):
                csv_data += f"{dates[i]},{temp_max[i]},{temp_min[i]},{temp_mean[i]},{precip[i]},{windspeed[i]},{winddir[i]}\n"
            
            # Save raw data to file
            output_file = f"data/{ville_name}_{start_date}_{end_date}.csv"
            with open(output_file, 'w') as f:
                f.write(csv_data)
            
            print(f"Saved data to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            print(traceback.format_exc())
            return False
    
    def process_weather_data(self, ville_name, file_path):
        """Process weather data from CSV file."""
        import pandas as pd
        import sqlite3
        import os
        import traceback
        
        print(f"Processing {file_path} for {ville_name}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Check if this is from Open-Meteo API
            if 'temp_max' in df.columns and 'temp_min' in df.columns:
                # Process Open-Meteo data format
                processed_data = []
                
                # Map Open-Meteo columns to our format
                for _, row in df.iterrows():
                    date_str = row['date']
                    
                    # Add temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE',
                        'Value': row['temp_mean']
                    })
                    
                    # Add min temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 00:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE_MIN',
                        'Value': row['temp_min']
                    })
                    
                    # Add max temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 00:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE_MAX',
                        'Value': row['temp_max']
                    })
                    
                    # Add wind speed data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'WIND_SPEED',
                        'Value': row['windspeed']
                    })
                    
                    # Add precipitation data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'PRECIPITATION',
                        'Value': row['precipitation']
                    })
                
                # Create DataFrame from processed data
                processed_df = pd.DataFrame(processed_data)
                
            elif 'name' in df.columns and 'datetime' in df.columns:
                # Process Visual Crossing data format
                processed_data = []
                
                # Map Visual Crossing columns to our format
                for _, row in df.iterrows():
                    date_str = row['datetime']
                    
                    # Add temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE',
                        'Value': row['temp']
                    })
                    
                    # Add min temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 00:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE_MIN',
                        'Value': row['tempmin']
                    })
                    
                    # Add max temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 00:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE_MAX',
                        'Value': row['tempmax']
                    })
                    
                    # Add humidity data if available
                    if 'humidity' in row:
                        processed_data.append({
                            'Datetime': f"{date_str} 12:00:00",
                            'BAT': ville_name,
                            'Type': 'HUMIDITY',
                            'Value': row['humidity']
                        })
                    
                    # Add wind speed data if available
                    if 'windspeed' in row:
                        processed_data.append({
                            'Datetime': f"{date_str} 12:00:00",
                            'BAT': ville_name,
                            'Type': 'WIND_SPEED',
                            'Value': row['windspeed']
                        })
                
                # Create DataFrame from processed data
                processed_df = pd.DataFrame(processed_data)
                
            else:
                # Original format (historique-meteo.net)
                # Assuming CSV format: date,temp_max,temp_min,etc.
                df.columns = ['Date', 'TempMax', 'TempMin', 'WindSpeed', 'WindGust', 'WindDir', 
                            'Precipitation', 'PressureMax', 'PressureMin', 'HumidityMax', 'HumidityMin',
                            'Visibility', 'CloudCover', 'HeatIndexMax', 'HeatIndexMin', 'DewPointMax',
                            'DewPointMin', 'WindChillMin', 'Sunrise', 'Sunset', 'MoonriseTime',
                            'MoonsetTime', 'MoonPhase', 'UVIndex']
                
                # Process data
                processed_data = []
                
                for _, row in df.iterrows():
                    date_str = row['Date']
                    
                    # Add temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE',
                        'Value': (row['TempMax'] + row['TempMin']) / 2  # Average temperature
                    })
                    
                    # Add min temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 00:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE_MIN',
                        'Value': row['TempMin']
                    })
                    
                    # Add max temperature data
                    processed_data.append({
                        'Datetime': f"{date_str} 00:00:00",
                        'BAT': ville_name,
                        'Type': 'TEMPERATURE_MAX',
                        'Value': row['TempMax']
                    })
                    
                    # Add humidity data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'HUMIDITY',
                        'Value': (row['HumidityMax'] + row['HumidityMin']) / 2  # Average humidity
                    })
                    
                    # Add wind speed data
                    processed_data.append({
                        'Datetime': f"{date_str} 12:00:00",
                        'BAT': ville_name,
                        'Type': 'WIND_SPEED',
                        'Value': row['WindSpeed']
                    })
                
                # Create DataFrame from processed data
                processed_df = pd.DataFrame(processed_data)
            
            # Store data in database
            success = self.store_weather_data(processed_df)
            
            if not success:
                print(f"Failed to store weather data for {ville_name}")
                return False
                
            print(f"Stored {len(processed_df)} weather data points for {ville_name}")
            return True
            
        except Exception as e:
            import traceback
            print(f"Error processing weather data: {e}")
            print(traceback.format_exc())
            return False
    
    def generate_visualizations(self, ville_name, viz_dir):
        """
        Generate visualizations for the weather data.
        
        Args:
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualizations
            
        Returns:
            pandas.DataFrame: DataFrame containing the weather data
        """
        try:
            print(f"Generating visualizations for {ville_name}")
            
            # Connect to database
            conn = sqlite3.connect('smarthome.db')
            
            # Query for weather data
            query = """
                SELECT Datetime, Type, Value
                FROM history
                WHERE BAT = ?
                ORDER BY Datetime
            """
            
            # Execute query
            df = pd.read_sql_query(query, conn, params=(ville_name,))
            
            # Close connection
            conn.close()
            
            if df.empty:
                print(f"No data found for {ville_name}")
                return pd.DataFrame()
            
            # Convert datetime to pandas datetime
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            
            # Generate visualizations
            self._generate_temperature_viz(df, ville_name, viz_dir)
            self._generate_precipitation_viz(df, ville_name, viz_dir)
            self._generate_wind_viz(df, ville_name, viz_dir)
            self._generate_consumption_viz(df, ville_name, viz_dir)
            self._generate_device_consumption_viz(df, ville_name, viz_dir)
            self._generate_smart_home_dashboard(df, ville_name, viz_dir)
            
            return df
        except Exception as e:
            print(f"Error generating visualizations: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def _generate_temperature_viz(self, df, ville_name, viz_dir):
        """
        Generate temperature visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing the weather data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
        """
        try:
            # Filter for temperature data
            temp_df = df[df['Type'].isin(['TEMPERATURE', 'TEMPERATURE_MIN', 'TEMPERATURE_MAX'])]
            
            if temp_df.empty:
                print("No temperature data found")
                return
            
            # Pivot data
            pivot_df = temp_df.pivot(index='Datetime', columns='Type', values='Value')
            
            # Rename columns
            pivot_df.columns = ['Average', 'Maximum', 'Minimum'] if len(pivot_df.columns) == 3 else pivot_df.columns
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Plot data
            if 'Minimum' in pivot_df.columns:
                plt.fill_between(pivot_df.index, pivot_df['Minimum'], pivot_df['Maximum'], 
                                 alpha=0.2, color='blue', label='Temperature Range')
            
            if 'Average' in pivot_df.columns:
                plt.plot(pivot_df.index, pivot_df['Average'], 'b-', linewidth=2, label='Average Temperature')
            
            if 'Maximum' in pivot_df.columns:
                plt.plot(pivot_df.index, pivot_df['Maximum'], 'r--', linewidth=1, label='Maximum Temperature')
            
            if 'Minimum' in pivot_df.columns:
                plt.plot(pivot_df.index, pivot_df['Minimum'], 'g--', linewidth=1, label='Minimum Temperature')
            
            # Add labels and title
            plt.xlabel('Date')
            plt.ylabel('Temperature (°C)')
            plt.title(f'Temperature in {ville_name}')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Add data points
            for col in pivot_df.columns:
                plt.scatter(pivot_df.index, pivot_df[col], s=30, alpha=0.5)
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{viz_dir}/{ville_name}_temperature.png", dpi=100)
            plt.close()
            
            print(f"Temperature visualization saved to {viz_dir}/{ville_name}_temperature.png")
        except Exception as e:
            print(f"Error generating temperature visualization: {e}")
            traceback.print_exc()
    
    def _generate_precipitation_viz(self, df, ville_name, viz_dir):
        """
        Generate precipitation visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing the weather data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
        """
        try:
            # Filter for precipitation data
            precip_df = df[df['Type'] == 'PRECIPITATION']
            
            if precip_df.empty:
                print("No precipitation data found")
                return
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Plot data
            plt.bar(precip_df['Datetime'], precip_df['Value'], width=0.8, color='skyblue', alpha=0.7)
            
            # Add labels and title
            plt.xlabel('Date')
            plt.ylabel('Precipitation (mm)')
            plt.title(f'Precipitation in {ville_name}')
            plt.grid(True, alpha=0.3, axis='y')
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Add data points and values
            for i, row in precip_df.iterrows():
                if row['Value'] > 0:
                    plt.text(row['Datetime'], row['Value'] + 0.5, f"{row['Value']:.1f}", 
                             ha='center', va='bottom', fontsize=8)
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{viz_dir}/{ville_name}_precipitation.png", dpi=100)
            plt.close()
            
            print(f"Precipitation visualization saved to {viz_dir}/{ville_name}_precipitation.png")
        except Exception as e:
            print(f"Error generating precipitation visualization: {e}")
            traceback.print_exc()
    
    def _generate_wind_viz(self, df, ville_name, viz_dir):
        """
        Generate wind visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing the weather data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
        """
        try:
            # Filter for wind data
            wind_df = df[df['Type'] == 'WIND_SPEED']
            
            if wind_df.empty:
                print("No wind data found")
                return
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Plot data
            plt.plot(wind_df['Datetime'], wind_df['Value'], 'g-', linewidth=2)
            plt.fill_between(wind_df['Datetime'], 0, wind_df['Value'], alpha=0.2, color='green')
            
            # Add labels and title
            plt.xlabel('Date')
            plt.ylabel('Wind Speed (km/h)')
            plt.title(f'Wind Speed in {ville_name}')
            plt.grid(True, alpha=0.3)
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Add data points
            plt.scatter(wind_df['Datetime'], wind_df['Value'], s=30, color='green', alpha=0.7)
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{viz_dir}/{ville_name}_wind.png", dpi=100)
            plt.close()
            
            print(f"Wind visualization saved to {viz_dir}/{ville_name}_wind.png")
        except Exception as e:
            print(f"Error generating wind visualization: {e}")
            traceback.print_exc()
    
    def _generate_consumption_viz(self, df, ville_name, viz_dir):
        """
        Generate energy consumption visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing the smart home data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
        """
        try:
            # Filter for consumption data
            consumption_df = df[df['Type'].isin(['ELECTRICITY', 'GAS', 'WATER'])]
            
            if consumption_df.empty:
                print("No consumption data found")
                return
            
            # Pivot data
            pivot_df = consumption_df.pivot(index='Datetime', columns='Type', values='Value')
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Plot data for each consumption type
            if 'ELECTRICITY' in pivot_df.columns:
                plt.plot(pivot_df.index, pivot_df['ELECTRICITY'], 'r-', linewidth=2, label='Electricity (kWh)')
            
            if 'GAS' in pivot_df.columns:
                plt.plot(pivot_df.index, pivot_df['GAS'], 'b-', linewidth=2, label='Gas (m³)')
            
            if 'WATER' in pivot_df.columns:
                plt.plot(pivot_df.index, pivot_df['WATER'], 'g-', linewidth=2, label='Water (L)')
            
            # Add labels and title
            plt.xlabel('Date')
            plt.ylabel('Consumption')
            plt.title(f'Energy Consumption in {ville_name}')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Add data points
            for col in pivot_df.columns:
                plt.scatter(pivot_df.index, pivot_df[col], s=30, alpha=0.5)
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{viz_dir}/{ville_name}_consumption.png", dpi=100)
            plt.close()
            
            print(f"Consumption visualization saved to {viz_dir}/{ville_name}_consumption.png")
        except Exception as e:
            print(f"Error generating consumption visualization: {e}")
            traceback.print_exc()
    
    def _generate_device_consumption_viz(self, df, ville_name, viz_dir):
        """
        Generate device-specific consumption visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing the smart home data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
        """
        try:
            # Filter for device consumption data
            # Look for types that start with 'DEVICE_' or contain 'DEVICE'
            device_df = df[df['Type'].str.contains('DEVICE', case=False, na=False)]
            
            if device_df.empty:
                print("No device consumption data found")
                # Try to find any columns that might represent devices
                potential_devices = df[~df['Type'].isin(['TEMPERATURE', 'TEMPERATURE_MIN', 'TEMPERATURE_MAX', 
                                                      'PRECIPITATION', 'WIND_SPEED', 'HUMIDITY', 
                                                      'ELECTRICITY', 'GAS', 'WATER', 'INDOOR_TEMP'])]
                
                if not potential_devices.empty:
                    print(f"Found potential device data: {potential_devices['Type'].unique()}")
                    device_df = potential_devices
                else:
                    return
            
            # Get unique device types
            device_types = device_df['Type'].unique()
            print(f"Found device types: {device_types}")
            
            # Create figure
            plt.figure(figsize=(14, 8))
            
            # Create a color map for devices
            colors = plt.cm.tab20(np.linspace(0, 1, len(device_types)))
            
            # Plot data for each device
            for i, device_type in enumerate(device_types):
                device_data = device_df[device_df['Type'] == device_type]
                plt.plot(device_data['Datetime'], device_data['Value'], 
                         linestyle='-', linewidth=2, color=colors[i], 
                         label=device_type.replace('DEVICE_', '').title())
                
                # Add data points
                plt.scatter(device_data['Datetime'], device_data['Value'], 
                           s=30, color=colors[i], alpha=0.7)
            
            # Add labels and title
            plt.xlabel('Date')
            plt.ylabel('Consumption (kWh)')
            plt.title(f'Device-Specific Energy Consumption in {ville_name}')
            plt.grid(True, alpha=0.3)
            
            # Add legend with better placement
            if len(device_types) > 10:
                plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
            else:
                plt.legend(loc='best')
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{viz_dir}/{ville_name}_device_consumption.png", dpi=100)
            plt.close()
            
            print(f"Device consumption visualization saved to {viz_dir}/{ville_name}_device_consumption.png")
            
            # Create a pie chart showing total consumption by device
            self._generate_device_consumption_pie(device_df, ville_name, viz_dir)
            
        except Exception as e:
            print(f"Error generating device consumption visualization: {e}")
            traceback.print_exc()
    
    def _generate_device_consumption_pie(self, device_df, ville_name, viz_dir):
        """
        Generate a pie chart showing total consumption by device.
        
        Args:
            device_df (pandas.DataFrame): DataFrame containing device consumption data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
        """
        try:
            # Group by device type and sum values
            device_totals = device_df.groupby('Type')['Value'].sum().reset_index()
            
            # Sort by total consumption (descending)
            device_totals = device_totals.sort_values('Value', ascending=False)
            
            # Create figure
            plt.figure(figsize=(10, 10))
            
            # Create pie chart
            plt.pie(device_totals['Value'], 
                   labels=[t.replace('DEVICE_', '').title() for t in device_totals['Type']], 
                   autopct='%1.1f%%',
                   startangle=90,
                   shadow=True,
                   explode=[0.05 if i < 3 else 0 for i in range(len(device_totals))],  # Explode the top 3 slices
                   colors=plt.cm.tab20(np.linspace(0, 1, len(device_totals))))
            
            # Add title
            plt.title(f'Total Energy Consumption by Device in {ville_name}')
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            plt.axis('equal')
            
            # Save figure
            plt.tight_layout()
            plt.savefig(f"{viz_dir}/{ville_name}_device_consumption_pie.png", dpi=100)
            plt.close()
            
            print(f"Device consumption pie chart saved to {viz_dir}/{ville_name}_device_consumption_pie.png")
        except Exception as e:
            print(f"Error generating device consumption pie chart: {e}")
            traceback.print_exc()
    
    def _generate_smart_home_dashboard(self, df, ville_name, viz_dir):
        """
        Generate a comprehensive smart home dashboard visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing the smart home data
            ville_name (str): Name of the city
            viz_dir (str): Directory to save visualization
            
        Returns:
            pandas.DataFrame: DataFrame containing the weather data
        """
        try:
            print(f"Generating smart home dashboard for {ville_name}")
            
            # Create a figure with subplots
            fig, axs = plt.subplots(3, 1, figsize=(14, 15), gridspec_kw={'height_ratios': [1, 1, 1]})
            fig.suptitle(f'Smart Home Dashboard - {ville_name}', fontsize=16)
            
            # 1. Temperature Plot
            temp_df = df[df['Type'].isin(['TEMPERATURE', 'TEMPERATURE_MIN', 'TEMPERATURE_MAX', 'INDOOR_TEMP'])]
            if not temp_df.empty:
                # Pivot data
                pivot_df = temp_df.pivot(index='Datetime', columns='Type', values='Value')
                
                # Plot outdoor temperatures
                if 'TEMPERATURE' in pivot_df.columns:
                    axs[0].plot(pivot_df.index, pivot_df['TEMPERATURE'], 'b-', linewidth=2, label='Outdoor Temp')
                
                # Plot indoor temperature if available
                if 'INDOOR_TEMP' in pivot_df.columns:
                    axs[0].plot(pivot_df.index, pivot_df['INDOOR_TEMP'], 'r-', linewidth=2, label='Indoor Temp')
                
                # Plot min/max range if available
                if 'TEMPERATURE_MIN' in pivot_df.columns and 'TEMPERATURE_MAX' in pivot_df.columns:
                    axs[0].fill_between(pivot_df.index, pivot_df['TEMPERATURE_MIN'], pivot_df['TEMPERATURE_MAX'], 
                                    alpha=0.2, color='blue', label='Outdoor Temp Range')
                
                axs[0].set_ylabel('Temperature (°C)')
                axs[0].set_title('Temperature Comparison')
                axs[0].grid(True, alpha=0.3)
                axs[0].legend(loc='upper right')
            
            # 2. Energy Consumption Plot
            consumption_df = df[df['Type'].isin(['ELECTRICITY', 'GAS', 'WATER'])]
            if not consumption_df.empty:
                # Pivot data
                pivot_df = consumption_df.pivot(index='Datetime', columns='Type', values='Value')
                
                # Plot each consumption type
                if 'ELECTRICITY' in pivot_df.columns:
                    axs[1].plot(pivot_df.index, pivot_df['ELECTRICITY'], 'r-', linewidth=2, label='Electricity (kWh)')
                
                if 'GAS' in pivot_df.columns:
                    axs[1].plot(pivot_df.index, pivot_df['GAS'], 'b-', linewidth=2, label='Gas (m³)')
                
                if 'WATER' in pivot_df.columns:
                    axs[1].plot(pivot_df.index, pivot_df['WATER'], 'g-', linewidth=2, label='Water (L)')
                
                axs[1].set_ylabel('Consumption')
                axs[1].set_title('Energy Consumption')
                axs[1].grid(True, alpha=0.3)
                axs[1].legend(loc='upper right')
            
            # 3. Weather Conditions Plot
            weather_df = df[df['Type'].isin(['PRECIPITATION', 'WIND_SPEED', 'HUMIDITY'])]
            if not weather_df.empty:
                # Create twin axis for different scales
                ax3 = axs[2]
                ax3_twin = ax3.twinx()
                
                # Pivot data
                pivot_df = weather_df.pivot(index='Datetime', columns='Type', values='Value')
                
                # Plot precipitation as bars
                if 'PRECIPITATION' in pivot_df.columns:
                    ax3.bar(pivot_df.index, pivot_df['PRECIPITATION'], width=0.02, color='skyblue', alpha=0.7, label='Precipitation (mm)')
                    ax3.set_ylabel('Precipitation (mm)', color='blue')
                
                # Plot wind speed as line on twin axis
                if 'WIND_SPEED' in pivot_df.columns:
                    ax3_twin.plot(pivot_df.index, pivot_df['WIND_SPEED'], 'g-', linewidth=2, label='Wind Speed (km/h)')
                    ax3_twin.set_ylabel('Wind Speed (km/h)', color='green')
                
                # Plot humidity if available
                if 'HUMIDITY' in pivot_df.columns:
                    ax3_twin.plot(pivot_df.index, pivot_df['HUMIDITY'], 'r-', linewidth=2, label='Humidity (%)')
                
                ax3.set_title('Weather Conditions')
                ax3.grid(True, alpha=0.3)
                
                # Create combined legend
                lines1, labels1 = ax3.get_legend_handles_labels()
                lines2, labels2 = ax3_twin.get_legend_handles_labels()
                ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
            
            # Format x-axis for all subplots
            for ax in axs:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Adjust layout
            plt.tight_layout()
            plt.subplots_adjust(top=0.95)
            
            # Save figure
            plt.savefig(f"{viz_dir}/{ville_name}_dashboard.png", dpi=100)
            plt.close()
            
            print(f"Smart home dashboard saved to {viz_dir}/{ville_name}_dashboard.png")
        except Exception as e:
            print(f"Error generating smart home dashboard: {e}")
            traceback.print_exc()

def main():
    # Define cities
    villes = [
        {'ville_name': 'Paris', 'start_date': '2022-01-01', 'end_date': '2022-12-31'}
    ]
    
    # Create fetcher
    try:
        fetcher = WeatherDataFetcher()
        
        # Process each city
        for ville in villes:
            success = fetcher.fetch_weather_data(
                ville_name=ville['ville_name'],
                start_date=ville['start_date'],
                end_date=ville['end_date']
            )
            
            if success:
                # Process weather data
                fetcher.process_weather_data(ville['ville_name'], f"data/{ville['ville_name']}_{ville['start_date']}_{ville['end_date']}.csv")
                
                # Generate visualizations
                fetcher.generate_visualizations(ville['ville_name'], 'visualizations')
            else:
                print(f"Failed to fetch data for {ville['ville_name']}")
        
        print("Weather data processing complete!")
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
