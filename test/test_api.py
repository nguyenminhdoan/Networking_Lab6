import requests
import base64

with open("dog.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

res = requests.post("https://<your-api-url>/upload", json={
    "filename": "dog.jpg",
    "file": img_b64
})
print(res.json())
