import requests

r1 = requests.post(url='http://127.0.0.1:8000/api/v13/user/')
print(r1.text)

