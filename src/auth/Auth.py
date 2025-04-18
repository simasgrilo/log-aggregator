import base64
from flask import Blueprint
from src.services.auth_service import AuthService

auth_bp = Blueprint("Auth",__name__)

@auth_bp.post("/register")
def register_user():
    """
    Endpoint to register a new user. Only the admin user can create new users. see User.py for more details.
    Returns:
        json.dumps(message): a payload representing success, if everything is ok, error otherwise
    """
    return AuthService.register_user()

@auth_bp.get("/login")
def login():
    """
    This endpoint will authenticate the user and create the token, returning a JWT pair (header, payload) cryptographed as standard with HS256
    """
    return AuthService.login()
