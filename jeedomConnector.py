import requests

JEEDOM_URL = "https://h2o.eu.jeedom.link/"
JEEDOM_API_KEY = "AnxyTteWw8DlvZqHQ1rnVFYuRR7NbXN0"

def get_jeedom_data(cmd_id="1"):
    """Minimal example to fetch data from Jeedom."""
    endpoint = f"{JEEDOM_URL}/core/api/jeeApi.php"
    params = {
        "apikey": JEEDOM_API_KEY,
        "type": "cmd",
        "id": cmd_id
    }
    response = requests.get(endpoint, params=params)
    data = response.json()
    return data

if __name__ == "__main__":
    data = get_jeedom_data()
    print(data)
