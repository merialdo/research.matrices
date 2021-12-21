import requests

url = 'http://localhost:5000'
img = open('EXAMPLE.jpg', 'rb')
files = {'file': img }
x = requests.post(url, files=files)
print(x.json())