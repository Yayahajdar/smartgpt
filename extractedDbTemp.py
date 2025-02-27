import sqlite3
import pandas as pd

DB_NAME = "SmartHome.db"

def import_csv_to_db(csv_file_path):
    """Reads CSV and imports data into SQLite 'measures' table."""
    # Example CSV with columns: timestamp,value
    df = pd.read_csv(csv_file_path)

    # Add a building column or other transformations as needed
    df['building'] = 'BAT'  # Example fixed building name

    # Connect to DB
    conn = sqlite3.connect(DB_NAME)
    # Append to 'measures' table
    df.to_sql('measures', conn, if_exists='append', index=False)
    conn.close()

if __name__ == '__main__':
    # Example usage
    csv_file_path = "historical_data.csv"
    import_csv_to_db(csv_file_path)
    print("CSV data imported successfully.")
