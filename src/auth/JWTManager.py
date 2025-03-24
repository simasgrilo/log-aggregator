from flask_jwt_extended import JWTManager


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