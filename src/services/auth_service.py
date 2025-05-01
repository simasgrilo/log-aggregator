import base64
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt
from src.models import User
from src.auth.PayloadValidator import PayloadValidator
from src.auth.Constants import Constants as AuthConstants
from src.Utils import Constants


class AuthService:
    """
    Authentication logic used by the logging facilities to authenticate the entity sending logs to the aggregator.
    Decoupled from the blueprint definition due to the usage of flask-restx to document the API using Swagger, so
    this avoids duplicate logic and centralizes the same logic used by both endpoints.
    Returns:
        _type_: _description_
    """
    
    @staticmethod
    @jwt_required()
    def register_user():
        """
        Endpoint to register a new user. Only the admin user can create new users. see User.py for more details.
        Returns:
            json.dumps(message): a payload representing success, if everything is ok, error otherwise
        """
        try:
            claims = get_jwt()
            if AuthConstants.CLAIM_CREATE_USER.value not in claims["perm"]:
                return jsonify({
                    "message": AuthConstants.MISSING_AUTH.value
                }), Constants.HTTP_UNAUTHORIZED.value
            data = request.json
            PayloadValidator.validate_payload(data)
            user = User.by_id(data['username'])
        except (ValueError, KeyError):
            #maybe protecting this against XSS/SQL injection attacks is a good thing...
            return jsonify({
                "message": "Illegal argument in your request. Please check your input"
            }), Constants.HTTP_BAD_REQUEST.value
        if user:
            return jsonify({
                "message" : "User already exists"
            }), Constants.HTTP_CONFLICT.value
        new_user = User(
            username=data['username']
        )
        new_user.set_password(data['password'])
        new_user.save()    
        return jsonify({"message": "user created",
                        "username": new_user.username
                    }), Constants.HTTP_CREATED.value

    @staticmethod
    def login():
        """
        This endpoint will authenticate the user and create the token, returning a JWT pair (header, payload) cryptographed as standard with HS256
        """
        try:
            request_user, request_password = str(base64.b64decode((request.headers.get("Authorization").split(" ")[1])), encoding="utf-8").split(":")
            user = User.by_id(request_user)
            if not user or not User.validate_password(user, request_password):
                return jsonify({
                    "error" : "invalid username or password. check your input payload"
                }), Constants.HTTP_BAD_REQUEST.value
            access_token = AuthService._add_additional_claims(user.username)
            refresh_token = create_refresh_token(identity=user.username)
            return jsonify({
                "message" : "Logged in",
                "token" : {
                    "access": access_token,
                    "refresh": refresh_token
                }
            }), Constants.HTTP_OK.value
        except (KeyError, AttributeError):
            return jsonify({
                "error": "one or more required fields were not provided. Check your input payload"
            }), Constants.HTTP_BAD_REQUEST.value
        except ValueError:
            return jsonify({
                "error": "Invalid Authorization parameters"
            }), Constants.HTTP_UNAUTHORIZED.value

    @staticmethod
    def _add_additional_claims(username: str):
        additional_claims = {
            "perm" : ["log"]
        }
        if username == 'admin':
            additional_claims["perm"].append("create_user")
        return create_access_token(identity=username, additional_claims=additional_claims)
    
    @staticmethod
    @jwt_required()
    def change_password():
        """
        Endpoint to allow chaning the password of an user. Only users with admin privileges can perform this acction
        Args:
        """
        try:
            data = request.json
            claims = get_jwt()
            if claims["sub"] != data["username"]:
                return jsonify({
                    "message": "Invalid token for the provided username."
                }), Constants.HTTP_UNAUTHORIZED.value
            user = AuthService.get_user()
            user.set_password(data['password'])
            user.save()
            return jsonify({
                "message": f'Password changed for user {user.username}'
            }), Constants.HTTP_OK.value
        except KeyError as e:
            return jsonify({
                "message": str(e)
            }), Constants.HTTP_BAD_REQUEST.value
        except ValueError:
            return jsonify({
                "message": AuthConstants.MISSING_AUTH.value
            }), Constants.HTTP_UNAUTHORIZED.value
    
    @staticmethod
    @jwt_required()
    def delete_user():
        """
        Endpoint to allow deletion of an user. Only users with admin rights can access this resource.
        """
        try:
            user = AuthService.get_user()
            claims = get_jwt()
            if AuthConstants.CLAIM_CREATE_USER.value not in claims["perm"]:
                return jsonify({
                    "message": AuthConstants.MISSING_AUTH.value
                }), Constants.HTTP_UNAUTHORIZED.value
            user.delete()
            return jsonify({
                "message": "User deleted"
            }), Constants.HTTP_OK.value
        except KeyError as e:
            return jsonify({
                "message": str(e)
            }), Constants.HTTP_BAD_REQUEST.value

    @staticmethod
    def get_user():
        """Retrieves the user that will have their password changed"""
        data = request.json
        PayloadValidator.validate_payload(data)
        user = User.by_id(data['username'])
        if not user:
            raise KeyError("User not found")
        return user
