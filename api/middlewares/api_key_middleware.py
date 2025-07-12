# NOTE: This middleware is no longer used. Kept for reference.
# Authorization now handled using JWT in route dependencies.



# import os
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# from starlette.responses import JSONResponse


# class APIKeyMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         # Skip API key check for OPTIONS (preflight) requests 
#         if request.method == "OPTIONS":
#             return await call_next(request)
#         # Skip API key check for the API documentation
#         excluded_paths = ["/docs", "/redoc", "/openapi.json"]
#         if request.url.path in excluded_paths:
#             response = await call_next(request)
#             return response
#         authorization = request.headers.get("Authorization")
#         if not authorization or not authorization.startswith("Bearer "):
#             return JSONResponse(
#                 content={"error": "Invalid or missing authorization header"},
#                 status_code=401,
#             )
#         elif authorization.split("Bearer ")[1].strip() != os.getenv("API_SERVER_KEY"):
#             return JSONResponse(
#                 content={"error": "Unauthorized. Invalid API key"},
#                 status_code=401,
#             )
#         response = await call_next(request)
#         return response







from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import os

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight without auth
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            return response

        # Skip API key check for docs
        excluded_paths = ["/docs", "/redoc", "/openapi.json"]
        if request.url.path in excluded_paths:
            response = await call_next(request)
        else:
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return JSONResponse(
                    content={"error": "Invalid or missing authorization header"},
                    status_code=401,
                )
            elif authorization.split("Bearer ")[1].strip() != os.getenv("API_SERVER_KEY"):
                return JSONResponse(
                    content={"error": "Unauthorized. Invalid API key"},
                    status_code=401,
                )
            response = await call_next(request)

        # ✅ Always add CORS headers to responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response
