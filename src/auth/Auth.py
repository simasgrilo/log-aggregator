from flask import Blueprint, request
from src.models import User
from .PayloadValidator import PayloadValidator
from src.Utils import Constants
import json

auth_bp = Blueprint("Auth",__name__)

@auth_bp.post("/register")
def register_user():
    """useless for us: only admin can create users."""
    
    try:
        data = request.json
        PayloadValidator.validate_payload(data)
        user = User.by_id(data['username'])
    except ValueError:
        #TODO convert this to a validation error: means that the payload does not match the schema defined. it also will validate for XSQL injection attacks
        return json.dumps({
            "message": "Illegal argument in your request. Please check your input"
        }), Constants.HTTP_BAD_REQUEST.value
    # except Exception:
    #     return json.dumps({
    #         "message" : "An internal error occured. Please contact your adminstrator"
    #     }), Constants.HTTP_INTERNAL_SERVER_ERROR.value
    if user:
        return json.dumps({
            "message" : "User already exists"
        }), Constants.HTTP_BAD_REQUEST.value
    
    new_user = User(
        username=data['username']
    )
    new_user.set_password(data['password'])
    new_user.save()    
    return json.dumps("message: user created")