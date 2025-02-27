import os
import re
import json
import datetime
import sqlite3
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# -----------------------------
# Configuration
# -----------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smarthome.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'  # Use environment variable in production
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# -----------------------------
# ORM Models
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Measure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Float, nullable=False)
    # Add additional columns (e.g., sensor_id, energy, occupancy) as needed

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ville_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)

# -----------------------------
# Routes for Authentication
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('signup'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. Please login.")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for('index'))

# -----------------------------
# Dashboard & Visualization
# -----------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))
    
    measures = Measure.query.order_by(Measure.timestamp.asc()).all()
    labels = [m.timestamp.strftime("%Y-%m-%d %H:%M:%S") for m in measures]
    values = [m.value for m in measures]

    return render_template('dashboard.html', labels=json.dumps(labels), values=json.dumps(values), measures=measures)



# -----------------------------
# CSV Import Route (Multiple CSV Files)
# -----------------------------
@app.route('/import_csv', methods=['GET', 'POST'])
def import_csv():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get the list of files from the form
        files = request.files.getlist('files')
        if not files:
            flash("No files selected")
            return redirect(url_for('import_csv'))
        
        for file in files:
            if file.filename == "":
                continue
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            try:
                # Assume CSV has at least columns: 'timestamp' and 'value'
                df = pd.read_csv(filepath)
                for _, row in df.iterrows():
                    ts = pd.to_datetime(row['timestamp'])
                    value = float(row['value'])
                    measure = Measure(timestamp=ts, value=value)
                    db.session.add(measure)
                db.session.commit()
                flash(f"Imported {file.filename} successfully")
            except Exception as e:
                flash(f"Error processing {file.filename}: {e}")
        return redirect(url_for('dashboard'))
    return render_template('import_csv.html')

# -----------------------------
# CSV Processing and Visualization
# -----------------------------
@app.route('/process_csv', methods=['GET', 'POST'])
def process_csv():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))
    
    # Get list of uploaded CSV files
    upload_folder = app.config['UPLOAD_FOLDER']
    csv_files = []
    try:
        csv_files = [os.path.join(upload_folder, f) for f in os.listdir(upload_folder) 
                    if f.endswith('.csv') and os.path.isfile(os.path.join(upload_folder, f))]
    except Exception as e:
        flash(f"Error accessing upload folder: {str(e)}")
    
    if request.method == 'POST':
        selected_files = request.form.getlist('selected_files')
        
        if not selected_files:
            flash("No files selected")
            return redirect(url_for('process_csv'))
        
        # Create full paths for selected files
        selected_file_paths = []
        for f in selected_files:
            file_path = os.path.join(upload_folder, f)
            if os.path.exists(file_path):
                selected_file_paths.append(file_path)
            else:
                flash(f"File not found: {f}")
        
        if not selected_file_paths:
            flash("No valid files selected")
            return redirect(url_for('process_csv'))
        
        # Create visualizations directory if it doesn't exist
        viz_dir = os.path.join(os.path.dirname(__file__), 'static', 'visualizations')
        os.makedirs(viz_dir, exist_ok=True)
        
        try:
            # Import the CSV processor
            from csv_processor import CSVProcessor
            
            # Process the selected CSV files
            processor = CSVProcessor(selected_file_paths)
            cleaned_data = processor.process_all(viz_dir)
            
            # Get list of generated visualization files
            viz_files = []
            for root, _, files in os.walk(viz_dir):
                for file in files:
                    if file.endswith(('.png', '.html')):
                        rel_path = os.path.join('visualizations', file)
                        viz_files.append({
                            'name': file,
                            'path': rel_path,
                            'is_html': file.endswith('.html')
                        })
            
            flash("CSV processing completed successfully!")
            return render_template('visualizations.html', visualizations=viz_files)
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error processing CSV files: {str(e)}\n{error_details}")
            flash(f"Error processing CSV files: {str(e)}")
            return redirect(url_for('process_csv'))
    
    return render_template('process_csv.html', csv_files=[os.path.basename(f) for f in csv_files])

# -----------------------------
# Weather Data Route (Visual Crossing API)
# -----------------------------
@app.route('/get_weather')
def get_weather():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))

    # Retrieve measures for visualization
    measures = Measure.query.order_by(Measure.timestamp.asc()).all()
    labels = [m.timestamp.strftime("%Y-%m-%d %H:%M:%S") for m in measures]
    values = [m.value for m in measures]
    
    # Use the date range from the measures table, if available
    first_measure = Measure.query.order_by(Measure.timestamp.asc()).first()
    last_measure = Measure.query.order_by(Measure.timestamp.desc()).first()
    if first_measure and last_measure:
        start_date = first_measure.timestamp.strftime('%Y-%m-%d')
        end_date = last_measure.timestamp.strftime('%Y-%m-%d')
    else:
        start_date = end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    WEATHER_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
    WEATHER_API_KEY = "JA8HYFV9Y52AAS4GGQ4QME87P"
    CITY = "Tours,FR"
    url = f"{WEATHER_URL}{CITY}/{start_date}/{end_date}?key={WEATHER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.json()
    except Exception as e:
        flash(f"Error fetching weather data: {e}")
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html', labels=json.dumps(labels), values=json.dumps(values), measures=measures, weather=weather_data)


# -----------------------------
# Jeedom Data Route (Example)
# -----------------------------
@app.route('/get_jeedom')
def get_jeedom():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))
    
    # Retrieve measures for visualization
    measures = Measure.query.order_by(Measure.timestamp.asc()).all()
    labels = [m.timestamp.strftime("%Y-%m-%d %H:%M:%S") for m in measures]
    values = [m.value for m in measures]
    
    JEEDOM_URL = "https://h2o.eu.jeedom.link/"
    JEEDOM_API_KEY = "AnxyTteWw8DlvZqHQ1rnVFYuRR7NbXN0"
    endpoint = f"{JEEDOM_URL}/core/api/jeeApi.php"
    params = {"apikey": JEEDOM_API_KEY, "type": "cmd", "id": "1"}
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        jeedom_data = response.json()
    except Exception as e:
        flash(f"Error fetching Jeedom data: {e}")
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html', labels=json.dumps(labels), values=json.dumps(values), measures=measures, jeedom=jeedom_data)

# -----------------------------
# Historical Weather Data Route
# -----------------------------
@app.route('/historical_weather', methods=['GET', 'POST'])
def historical_weather():
    """
    Route for fetching and displaying historical weather data.
    """
    # Import required modules
    from weather_data_fetcher import WeatherDataFetcher
    from datetime import datetime
    
    # Use hardcoded list of cities instead of querying database
    villes = [
        {'id': 'Paris', 'name': 'Paris'},
        {'id': 'Tours', 'name': 'Tours'},
        {'id': 'val de Roland', 'name': 'val de Roland'},
      
    ]
    
    # Get current year for form
    current_year = datetime.now().year
    
    if request.method == 'POST':
        try:
            # Get form data
            ville = request.form.get('ville')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
            print(f"Form data received: ville={ville}, start_date={start_date}, end_date={end_date}")
            
            # Validate inputs
            if not ville or not start_date or not end_date:
                flash('Please fill all required fields', 'danger')
                return redirect(url_for('historical_weather'))
            
            # Get ville name (same as ID for our hardcoded cities)
            ville_name = ville
            print(f"Using ville_name: {ville_name}")
            
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Create visualizations directory if it doesn't exist
            viz_dir = 'static/visualizations'
            os.makedirs(viz_dir, exist_ok=True)
            
            # Create weather data fetcher
            fetcher = WeatherDataFetcher()
            
            # Fetch weather data
            print(f"Calling fetch_weather_data with ville_name={ville_name}, start_date={start_date}, end_date={end_date}")
            success = fetcher.fetch_weather_data(
                ville_name=ville_name,
                start_date=start_date,
                end_date=end_date
            )
            
            if not success:
                print("fetch_weather_data returned False")
                # Check if start date is after end date
                from datetime import datetime
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                    if start_date_obj > end_date_obj:
                        flash('Start date must be before or equal to end date.', 'danger')
                    else:
                        flash('Failed to fetch weather data. Please try again.', 'danger')
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD format.', 'danger')
                
                return redirect(url_for('historical_weather'))
            
            # Process weather data
            file_path = f"data/{ville_name}_{start_date}_{end_date}.csv"
            print(f"Calling process_weather_data with ville_name={ville_name}, file_path={file_path}")
            success = fetcher.process_weather_data(ville_name, file_path)
            
            if not success:
                print("process_weather_data returned False")
                flash('Failed to process weather data. Please try again.', 'danger')
                return redirect(url_for('historical_weather'))
            
            # Generate visualizations
            print(f"Calling generate_visualizations with ville_name={ville_name}, viz_dir={viz_dir}")
            df = fetcher.generate_visualizations(ville_name, viz_dir)
            
            if df.empty:
                print("generate_visualizations returned empty DataFrame")
                flash('No data was processed. Please try again.', 'danger')
                return redirect(url_for('historical_weather'))
            
            # Redirect to weather display page
            return redirect(url_for('display_weather', ville_name=ville_name, start_date=start_date, end_date=end_date))
        except Exception as e:
            print(f"Exception in historical_weather route: {e}")
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('historical_weather'))
    
    return render_template('historical_weather.html', villes=villes, current_year=current_year)

@app.route('/check_weather_status/<ville_name>/<start_date>/<end_date>')
def check_weather_status(ville_name, start_date, end_date):
    """
    Check weather data processing status for a given city and date range.
    """
    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Check if weather data exists for this range
        weather_data = db.session.query(WeatherData).filter(
            WeatherData.ville_name == ville_name,
            WeatherData.date >= start_date,
            WeatherData.date <= end_date
        ).first()
        
        if weather_data:
            return jsonify({
                'status': 'complete',
                'message': 'Weather data already processed'
            })
        else:
            return jsonify({
                'status': 'pending', 
                'message': 'Weather data not yet processed'
            })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/display_weather/<ville_name>/<start_date>/<end_date>')
def display_weather(ville_name, start_date, end_date):
    """
    Route for displaying weather data.
    """
    import pandas as pd
    import sqlite3
    
    try:
        # Connect to database
        conn = sqlite3.connect('smarthome.db')
        
        # Query for weather data
        query = """
            SELECT Datetime, Type, Value
            FROM history
            WHERE BAT = ?
            AND Type IN ('TEMPERATURE', 'TEMPERATURE_MIN', 'TEMPERATURE_MAX', 'PRECIPITATION', 'WIND_SPEED')
            ORDER BY Datetime
        """
        
        # Execute query
        df = pd.read_sql_query(query, conn, params=(ville_name,))
        
        # Query for device consumption data
        device_query = """
            SELECT Datetime, Type, Value
            FROM history
            WHERE BAT = ?
            AND (Type LIKE 'DEVICE%' OR Type NOT IN ('TEMPERATURE', 'TEMPERATURE_MIN', 'TEMPERATURE_MAX', 
                                                  'PRECIPITATION', 'WIND_SPEED', 'HUMIDITY', 
                                                  'ELECTRICITY', 'GAS', 'WATER', 'INDOOR_TEMP'))
            ORDER BY Datetime
        """
        
        # Execute device query
        device_df = pd.read_sql_query(device_query, conn, params=(ville_name,))
        
        # Close connection
        conn.close()
        
        if df.empty:
            flash('No weather data found.', 'danger')
            return redirect(url_for('historical_weather'))
        
        # Convert datetime to pandas datetime
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df['Date'] = df['Datetime'].dt.date
        
        # Organize data by date
        weather_data = {}
        summary = {
            'avg_temp': 0,
            'max_temp': -100,
            'total_precip': 0,
            'avg_wind': 0
        }
        
        temp_values = []
        wind_values = []
        
        # Process each row
        for _, row in df.iterrows():
            date_str = str(row['Date'])
            data_type = row['Type']
            value = row['Value']
            
            if date_str not in weather_data:
                weather_data[date_str] = {
                    'temp': 0,
                    'temp_min': 0,
                    'temp_max': 0,
                    'precipitation': 0,
                    'wind_speed': 0
                }
            
            if data_type == 'TEMPERATURE':
                weather_data[date_str]['temp'] = value
                temp_values.append(value)
                if value > summary['max_temp']:
                    summary['max_temp'] = value
            elif data_type == 'TEMPERATURE_MIN':
                weather_data[date_str]['temp_min'] = value
            elif data_type == 'TEMPERATURE_MAX':
                weather_data[date_str]['temp_max'] = value
            elif data_type == 'PRECIPITATION':
                weather_data[date_str]['precipitation'] = value
                summary['total_precip'] += value
            elif data_type == 'WIND_SPEED':
                weather_data[date_str]['wind_speed'] = value
                wind_values.append(value)
        
        # Calculate summary statistics
        if temp_values:
            summary['avg_temp'] = sum(temp_values) / len(temp_values)
        
        if wind_values:
            summary['avg_wind'] = sum(wind_values) / len(wind_values)
        
        # Sort weather data by date
        weather_data = {k: weather_data[k] for k in sorted(weather_data.keys())}
        
        # Process device consumption data
        device_data = {}
        
        if not device_df.empty:
            device_df['Datetime'] = pd.to_datetime(device_df['Datetime'])
            
            # Get total consumption across all devices
            total_consumption = device_df['Value'].sum()
            
            # Process each device type
            for device_type in device_df['Type'].unique():
                device_values = device_df[device_df['Type'] == device_type]['Value']
                
                device_data[device_type.replace('DEVICE_', '').title()] = {
                    'total': device_values.sum(),
                    'avg': device_values.mean(),
                    'max': device_values.max(),
                    'percentage': (device_values.sum() / total_consumption * 100) if total_consumption > 0 else 0
                }
        
        return render_template(
            'weather_display.html',
            ville_name=ville_name,
            start_date=start_date,
            end_date=end_date,
            weather_data=weather_data,
            summary=summary,
            device_data=device_data
        )
    
    except Exception as e:
        print(f"Exception in display_weather route: {e}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('historical_weather'))

# -----------------------------
# Sample Weather Data Route
# -----------------------------
@app.route('/process_sample_weather', methods=['POST'])
def process_sample_weather():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))
    
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Sample data file
        sample_file = os.path.join(data_dir, 'sample_weather_data.csv')
        
        # Check if the sample file exists
        if not os.path.exists(sample_file):
            flash("Sample data file not found. Please check the application setup.")
            return redirect(url_for('historical_weather'))
        
        # Create visualizations directory if it doesn't exist
        viz_dir = os.path.join(os.path.dirname(__file__), 'static', 'visualizations')
        os.makedirs(viz_dir, exist_ok=True)
        
        # Import the weather data fetcher
        from weather_data_fetcher import WeatherDataFetcher
        
        # Create fetcher
        fetcher = WeatherDataFetcher()
        
        # Process the sample data
        ville_name = "SampleCity"
        
        # Process the data
        fetcher.process_weather_data(ville_name, sample_file)
        
        # Generate visualizations
        df = fetcher.generate_visualizations(ville_name, viz_dir)
        
        if df.empty:
            flash("No data was processed from the sample file.")
            return redirect(url_for('historical_weather'))
        
        # Get list of generated visualization files for this city
        viz_files = []
        for root, _, files in os.walk(viz_dir):
            for file in files:
                if file.startswith(f"{ville_name}_") and file.endswith(('.png', '.html')):
                    rel_path = os.path.join('visualizations', file)
                    viz_files.append({
                        'name': file,
                        'path': rel_path,
                        'is_html': file.endswith('.html')
                    })
        
        if not viz_files:
            flash("No visualizations could be generated from the sample data.")
            return redirect(url_for('historical_weather'))
        
        flash(f"Sample weather data processed successfully!")
        return render_template('visualizations.html', 
                              visualizations=viz_files, 
                              title=f"Sample Weather Data Visualizations")
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing sample weather data: {str(e)}\n{error_details}")
        flash(f"Error processing sample weather data: {str(e)}")
        return redirect(url_for('historical_weather'))

# -----------------------------
# Import Sample Device Data Route
# -----------------------------
@app.route('/import_sample_device_data')
def import_sample_device_data():
    """
    Import sample device data from CSV file.
    """
    import pandas as pd
    import sqlite3
    import os
    
    try:
        # Check if file exists
        sample_file = os.path.join('data', 'sample_device_data.csv')
        if not os.path.exists(sample_file):
            flash('Sample device data file not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Read CSV file
        df = pd.read_csv(sample_file)
        
        # Connect to database
        conn = sqlite3.connect('smarthome.db')
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Datetime TEXT,
                BAT TEXT,
                Type TEXT,
                Value REAL
            )
        ''')
        
        # Insert data
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO history (Datetime, BAT, Type, Value)
                VALUES (?, ?, ?, ?)
            ''', (
                row['Datetime'],
                row['BAT'],
                row['Type'],
                row['Value']
            ))
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        
        flash('Sample device data imported successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        flash(f'Error importing sample device data: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# -----------------------------
# Import Sample Data Route
# -----------------------------
@app.route('/import_sample_data')
def import_sample_data():
    """
    Import sample weather data from CSV file.
    """
    import pandas as pd
    import sqlite3
    import os
    
    try:
        # Check if file exists
        sample_file = os.path.join('data', 'sample_weather_data.csv')
        if not os.path.exists(sample_file):
            flash('Sample weather data file not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Read CSV file
        df = pd.read_csv(sample_file)
        
        # Connect to database
        conn = sqlite3.connect('smarthome.db')
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS weather_data
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        temperature REAL NOT NULL,
                        humidity REAL NOT NULL)''')
        
        # Insert data
        for _, row in df.iterrows():
            cursor.execute('''INSERT INTO weather_data (timestamp, temperature, humidity)
                            VALUES (?, ?, ?)''',
                         (row['timestamp'], row['temperature'], row['humidity']))
        
        # Commit and close
        conn.commit()
        conn.close()
        
        flash('Sample weather data imported successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        flash(f'Error importing sample weather data: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# -----------------------------
# Main Entry Point
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
