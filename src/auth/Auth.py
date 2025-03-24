from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from src.models import User
from .PayloadValidator import PayloadValidator
from src.Utils import Constants

auth_bp = Blueprint("Auth",__name__)

@auth_bp.post("/register")
def register_user():
    """
    Endpoint to register a new user. Only the admin user can create new users. see User.py for more details.
    Returns:
        json.dumps(message): a payload representing success, if everything is ok, error otherwise
    """
    try:
        #headers = request.header #TODO implement the validation that only master user can create users. this can be done using JWT...
        data = request.json
        PayloadValidator.validate_payload(data)
        user = User.by_id(data['username'])
    except ValueError:
        #TODO convert this to a validation error: means that the payload does not match the schema defined. it also will validate for XSQL injection attacks
        return jsonify({
            "message": "Illegal argument in your request. Please check your input"
        }), Constants.HTTP_CONFLICT.value
    # except Exception:
    #     return json.dumps({
    #         "message" : "An internal error occured. Please contact your adminstrator"
    #     }), Constants.HTTP_INTERNAL_SERVER_ERROR.value
    if user:
        return jsonify({
            "message" : "User already exists"
        }), Constants.HTTP_BAD_REQUEST.value
    
    new_user = User(
        username=data['username']
    )
    new_user.set_password(data['password'])
    new_user.save()    
    return jsonify("message: user created")

@auth_bp.post("/login")
def login():
    """
    This endpoint will authenticate the user and create the token, returning a JWT pair
    """
    try:
        payload = request.json
        user = User.by_id(payload["username"])
        if not user or not User.validate_password(user, payload["password"]):
            return jsonify({
                "error" : "invalid username or password. check your input payload"
            }), Constants.HTTP_BAD_REQUEST.value
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)
        return jsonify({
            "message" : "Logged in",
            "token" : {
                "access": access_token,
                "refresh": refresh_token
            }
        }), Constants.HTTP_OK.value
    except KeyError:
        return jsonify({
            "error": "one or more required fields were not provided. Check your input payload"
        }), Constants.HTTP_BAD_REQUEST.value