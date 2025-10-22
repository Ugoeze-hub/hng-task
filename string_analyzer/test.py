import requests

response = requests.delete('http://localhost:8000/string-analyzer/strings/madam/')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")