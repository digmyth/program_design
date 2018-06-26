# import requests
#
# # r1 = requests.post(url='http://127.0.0.1:8000/api/v1/user/')
# # print(r1.text)
#
#
# r2 = requests.post(
#     url='http://127.0.0.1:8000/api/v1/auth/',
#     json={'username':'CTO','password':123},
#     headers = {'Content_Tyep':'application/json'},
# )
#
# print(r2.text)
# # wxq: 73b0bdbc-e35d-487a-ae79-807be86719b5
# # cto: d4adb2fd-03fd-4474-8822-2cb025a3e7d9

xx = '3/m'

def parse_rate(rate):
    num, period = rate.split('/')
    num_requests = int(num)
    duration = {'s':1,'m':60,'h':3600,'d':86400}[period[0]]
    print(num_requests,duration)

parse_rate(xx)

