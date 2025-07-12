from tests import client
from os import getenv


def test_health_check():
    response = client.get(
        "/api/health", headers={"Authorization": "Bearer " + getenv("API_SERVER_KEY")}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
