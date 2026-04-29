import requests

# Replace with your Plant.id API key
API_KEY = '48hPabkiFpXeCVmW650uD8HQNTw0ixexyPQEIyJ7wUDwGWmNAQ'

# URL for the Plant.id API
API_URL = 'https://plant.id/api/v3/identification'

# Path to the image file you want to identify
IMAGE_PATH = 'img.jpg'

# Read the image file
with open(IMAGE_PATH, 'rb') as file:
    image_data = file.read()

# Prepare the request payload
files = {'images': image_data}
headers = {'Api-Key': API_KEY}

# Send the request to the Plant.id API
response = requests.post(API_URL, files=files, headers=headers)

# Check if the request was successful
if response.status_code == 201:
    # Parse the JSON response
    result = response.json()
    
    # Extract the classification suggestions
    suggestions = result.get('result', {}).get('classification', {}).get('suggestions', [])
    
    if suggestions:
        print("Top suggestions for the plant:")
        for suggestion in suggestions:
            plant_name = suggestion.get('name', 'Unknown')
            probability = suggestion.get('probability', 0)
            print(f"- {plant_name} (Probability: {probability:.2f})")
    else:
        print("No suggestions found.")
else:
    print(f"Error: {response.status_code} - {response.text}")