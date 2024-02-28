import requests


response = requests.get("https://api.usemotion.com/v1/workspaces",
    headers={'X-API-Key': 'xx'})
json_response = response.json()
print(json_response)
