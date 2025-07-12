# from tests import client


# def test_health_check_invalid_key():
#     response = client.get(
#         "/api/health", headers={"Authorization": "Bearer " + "invalid_key"}
#     )
#     assert response.status_code == 401


# def test_health_check_missing_key():
#     response = client.get("/api/health")
#     assert response.status_code == 401
