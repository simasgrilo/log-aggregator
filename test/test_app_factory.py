import tempfile
import os
from json import JSONEncoder
from flask import Flask
from LogAggregator import LogAggregator
from src.auth import auth_bp, LogJWTManager as jwt
from src.blueprints import LogBlueprint
from src.database import DB as db
from src.models import User
from LogAggregator import LogAggregator
import gc


class TestAppFactory:
    """ Test class for LogAggregator - creates a test app considering the same routes and attributes as the original app
        It creates the LogAggregator object but replacing some of the attributes with mock values.
    """

    def __init__(self):
        self.tempfile = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.app = self.create_test_app()
        self.common_username = 'johndoe'
        self.common_username_password = 'mypass'
        with self.app.app_context():
            User.create_admin()
            self.new_user = User(
                username=self.common_username,
            )
            self.new_user.set_password(self.common_username_password)
            self.new_user.save()
        
    def get_credentials(self):
        return (self.common_username, self.common_username_password)

    def create_test_app(self):
        """
        Creates an subset of the Flask application that loads only the part of the app to be tested.
        """
        test_config = {
            "TESTING" : True,
            "SQLALCHEMY_DATABASE_URI" : f"sqlite:///{self.tempfile.name}",
            "JWT_SECRET_KEY" : "iamnotasafekey"
        }
        return LogAggregator(test_config=test_config).app
    
    def get_test_app(self):
        """
        Returns the current test factory instance. Required to be accessed in test scenarios.
        """
        return self.app
    
    
    def destroy_test_app(self):
        """
        Closes all the resources required by the test app, namely the database resource, and deletes the temporary file.
        """
        db.end_db(self.app)
        self.tempfile.close()
        try:
            if os.path.exists(self.tempfile.name):
                os.remove(self.tempfile.name)
        except (FileNotFoundError, PermissionError) as e:
            print(e)
    
