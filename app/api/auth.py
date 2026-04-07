from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.utils.auth import decode_access_token

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifies local JWT tokens and retrieves user information."""
    access_token = credentials.credentials
    try:
        payload = decode_access_token(access_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    auth_id = payload.get("sub")
    if not auth_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"id": auth_id}
