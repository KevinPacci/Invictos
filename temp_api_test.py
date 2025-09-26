from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
response = client.get("/bets")
print(response.status_code)
print(response.json())

