import requests

# r1 = requests.post(url='http://127.0.0.1:8000/api/v1/user/')
# print(r1.text)


r2 = requests.post(
    url='http://127.0.0.1:8000/api/v1/auth/',
    json={'username':'wxq','password':123},
    headers = {'Content_Tyep':'application/json'},
)

print(r2.text)
# bdb61a90-8f4a-4593-8639-9eb21ee2b946

