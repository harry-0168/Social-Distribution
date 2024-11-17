import requests

url = "https://social-distribution-dhruvil-7ee59df447bd.herokuapp.com/"

try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes (e.g., 404, 500)
    
    # Print the response (assuming the API returns JSON)
    print("Response Status Code:", response.status_code)
    print("Response Data:", response.json())  # Use .text if response is not JSON
except requests.RequestException as e:
    print("Error during request:", e)