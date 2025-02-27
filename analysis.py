import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

DB_NAME = "SmartHome.db"

def load_data():
    """Load measures from DB into a Pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM measures", conn)
    conn.close()
    return df

def train_model():
    """Simple example: train a regression model on the measures data."""
    df = load_data()
    
    # Suppose 'value' is what we want to predict
    # We'll create some dummy feature from the timestamp, etc.
    if df.empty:
        print("No data available to train.")
        return

    # For demonstration: convert timestamp to numeric or hour of day, etc.
    # e.g. parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    
    # Features and target
    X = df[['hour']]  # minimal feature
    y = df['value']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Model MSE: {mse:.2f}")

    # In real scenario, you might save the trained model to disk
    # e.g. with joblib or pickle
    # joblib.dump(model, "my_model.pkl")

if __name__ == "__main__":
    train_model()
