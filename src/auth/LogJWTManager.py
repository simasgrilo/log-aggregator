from flask_jwt_extended import JWTManager
from flask import jsonify


class LogJWTManager:
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogJWTManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._jwt = JWTManager()
    
    @classmethod
    def get_instance(cls):
        return cls._instance
            
    def get_jwt_manager(self):
        return self._jwt
    
    @staticmethod
    def initialize_manager(app):
        jwt_manager = LogJWTManager.get_instance()
        if not jwt_manager:
            jwt_manager = LogJWTManager()
        jwt_manager._jwt.init_app(app)
        LogJWTManager.expired_token(jwt_manager._jwt)
        LogJWTManager.invalid_token(jwt_manager._jwt)
        LogJWTManager.unauthorized_token(jwt_manager._jwt)
        
    #handlers
    def expired_token(jwt):
        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_data):
            return jsonify({"message" : "Token has expired", "error" : "expired_token"}), 401
        return expired_token_callback
    
    def invalid_token(jwt):
        @jwt.invalid_token_loader
        def invalid_token_callback(token):
            return jsonify({"message" : "Invalid token", "error" : "invalid_token"}), 401
        return invalid_token_callback

    def unauthorized_token(jwt):
        @jwt.unauthorized_loader
        def missing_token_callback(token):
            return jsonify({"message" : "Missing valid token", "error" : "missing_token"}), 401
        return missing_token_callback