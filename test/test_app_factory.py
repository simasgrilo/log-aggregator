
import tempfile
import os
from pathlib import Path
from json import JSONEncoder
from flask import Flask
from LogAggregator import LogAggregator
from src.auth import auth_bp, LogJWTManager as jwt
from src.database import DB as db
from src.models import User


class TestAppFactory:
    """ Test class for LogAggregator - creates a test app considering the same routes and attributes as the original app"""

    def __init__(self):
        directory = os.path.abspath(Path(__file__).parent)
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False, dir=directory)
        self.path = f"sqlite:///{self.temp_db_file.name}"
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
        self.app.config["JWT_SECRET_KEY"] = "iamnotasafekey"
        
    def get_credentials(self):
        return (self.common_username, self.common_username_password)

    def create_test_app(self):
        """
        Creates an subset of the Flask application that loads only the part of the app to be tested.
        """
        app = Flask(__name__)
        app.config.update({
            "TESTING" : True,
            "SQLALCHEMY_DATABASE_URI" : self.path
        })
        #TODO decouple the url_rule from LogAggregator to a Blueprint file...
        app.add_url_rule("/", "online", LogAggregator().online)
        app.add_url_rule("/log", "log", LogAggregator().log_service, methods=["POST"])
        app.register_blueprint(auth_bp,url_prefix='/auth')
        app.json_encoder = JSONEncoder
        db.initialize_db(app)
        jwt.initialize_manager(app)
        return app
    
    def get_test_app(self):
        """
        Returns the current app instance
        """
        return self.app
    
    def destroy_test_app(self):
        """
        Closes all the resources required by the test app, namely the database resource, and deletes the temporary file.
        """
        db.end_db(self.app)
        self.temp_db_file.close()
        try:
            if os.path.exists(self.temp_db_file.name):
                os.remove(self.temp_db_file.name)
        except (FileNotFoundError, PermissionError):
            pass
    
