import requests

url = "https://172.64.147.158/openai/v1/chat/completions"
headers = {"Host": "api.groq.com", "Authorization": f"Bearer YOUR_KEY"}

response = requests.post(url, headers=headers, json={
    "model": "llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": "Hello from Suraj"}]
}, verify=True)

print(response.text)
