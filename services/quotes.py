import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.api-ninjas.com/v2/randomquotes"


def fetch_random_quotes(categories=None, api_key=None):
    key = api_key or os.getenv("API_NINJAS_KEY")
    if not key:
        raise RuntimeError("API_NINJAS_KEY not found in environment or api_key param")

    params = {}
    if categories:
        if isinstance(categories, (list, tuple, set)):
            categories = ",".join(categories)
        params["categories"] = categories

    response = requests.get(
        API_URL,
        headers={"X-Api-Key": key},
        params=params,
        timeout=5,
    )

    response.raise_for_status()
    return response.json()


def fetch_random_quote(categories=None, api_key=None):
    quotes = fetch_random_quotes(categories=categories, api_key=api_key)
    if not isinstance(quotes, list) or not quotes:
        raise RuntimeError("Quote API returned no quotes")
    return quotes[0]


if __name__ == "__main__":
    print(fetch_random_quote())
