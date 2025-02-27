from kafka import KafkaConsumer
import sqlite3
import json

DB_NAME = "SmartHome.db"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "Measures"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def consume_kafka_messages():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        data = message.value
        # Example: data might look like {"timestamp": "...", "value": 123.45}
        timestamp = data.get("timestamp")
        value = data.get("value")

        # Store into SQLite
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO measures (timestamp, value) VALUES (?, ?)", (timestamp, value))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    consume_kafka_messages()
