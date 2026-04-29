import requests
from bs4 import BeautifulSoup

WIKIPEDIA_API_URL = 'https://en.wikipedia.org/w/api.php'
DETAILS_URL = "https://api.gbif.org/v1/species/{}"

def get_plant_details_wikipedia(plant_name):
    params = {
        'action': 'query',
        'format': 'json',
        'titles': plant_name,
        'prop': 'extracts',
        'exintro': True,  # Get only the introductory section
        'explaintext': True,  # Return plain text instead of HTML
    }
    response = requests.get(WIKIPEDIA_API_URL, params=params)
    
    if response.status_code == 200:
        pages = response.json().get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            return page_data.get('extract', 'No details found.')
    return 'No details found.'

import requests

BASE_URL = "https://api.gbif.org/v1/species/match"

def get_plant_details(plant_name):
    params = {
        "name": plant_name,
        "verbose": "true"
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if "scientificName" in data:
            species_key = data.get("usageKey", "N/A")
            print(f"Scientific Name: {data.get('scientificName', 'N/A')}")
            print(f"Kingdom: {data.get('kingdom', 'N/A')}")
            print(f"Phylum: {data.get('phylum', 'N/A')}")
            print(f"Class: {data.get('class', 'N/A')}")
            print(f"Order: {data.get('order', 'N/A')}")
            print(f"Family: {data.get('family', 'N/A')}")
            print(f"Genus: {data.get('genus', 'N/A')}")
            print(f"Species Key: {data.get('usageKey', 'N/A')}")
            print(f"More Info: https://www.gbif.org/species/{data.get('usageKey', 'N/A')}")

            if species_key != "N/A":
                common_name_response = requests.get(DETAILS_URL.format(species_key))
                if common_name_response.status_code == 200:
                    common_data = common_name_response.json()
                    common_name = common_data.get("vernacularName", "N/A")  # 'vernacularName' contains common name
                    print(f"Common Name: {common_name}")
        else:
            print("No plant found with that name.")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    plant_name = "Codiaeum variegatum"
    get_plant_details(plant_name)


    print(f"Fetching details for {plant_name} from Wikipedia...")
    details = get_plant_details_wikipedia(plant_name)
    
    if details:
        print(f"\nDetails about {plant_name}:\n{details}")
    else:
        print(f"No details found for {plant_name}.")


# Fetch and parse the Wikipedia page


    