import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.api-ninjas.com/v1/facts"


def fetch_random_facts(limit=1, api_key=None):
    key = api_key or os.getenv("API_NINJAS_KEY")
    if not key:
        raise RuntimeError("API_NINJAS_KEY not found in environment or api_key param")

    response = requests.get(
        API_URL,
        headers={"X-Api-Key": key},
        params={"limit": limit},
        timeout=5,
    )

    response.raise_for_status()
    return response.json()


def fetch_random_fact(api_key=None):
    facts = fetch_random_facts(limit=1, api_key=api_key)
    if not isinstance(facts, list) or not facts:
        raise RuntimeError("Facts API returned no facts")
    return facts[0]


if __name__ == "__main__":
    print(fetch_random_fact())
