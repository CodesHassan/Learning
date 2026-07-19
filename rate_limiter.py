# from slowapi import Limiter
# from fastapi import Request

# def get_user_key(request: Request):
#     user = getattr(request.state, "user", None)
#     if user and hasattr(user, "id"):
#         return str(user.id)
    
#     return request.client.host

# limiter = Limiter(key_func=get_user_key)


# from slowapi import Limiter
# from fastapi import Request
# import jwt, os

# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = "HS256"


# def get_user_key(request: Request):
#     token = request.headers.get("Authorization")

#     if token:
#         token = token.replace("Bearer ", "")

#         payload = jwt.decode(
#             token,
#             SECRET_KEY,
#             algorithms=[ALGORITHM]
#         )

#         return str(payload["_id"])

#     return request.client.host


# limiter = Limiter(
#     key_func=get_user_key
# )

from fastapi import FastAPI, Request, Depends, HTTPException
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

def get_user_key(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id") and user.id:
        return f"user:{user.id}"
    return f"ip:{get_remote_address(request)}"

limiter = Limiter(key_func=get_user_key, key_style="endpoint")