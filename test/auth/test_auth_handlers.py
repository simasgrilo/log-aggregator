"""
Test the JWT authentication handlers and whether the user creation endpoint is protected by JWT authentication.
"""
import unittest
import shutil
import os
import sys
import base64
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.abspath(Path(__file__).parent.parent.parent), "src"))
sys.path.insert(0, os.path.join(os.path.abspath(Path(__file__).parent.parent.parent)))
from LogAggregator import LogAggregator
from src.Utils import Constants
from src.models import User
from src.database import DB as db
from json import JSONEncoder

class Test_TestJWTAuthHandlers(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.source_file = os.path.join(os.path.abspath(Path(__file__).parent.parent), "config.json")
        cls.dest_file = os.path.join(os.path.abspath(Path(__file__).parent.parent.parent), "config.json")
        shutil.copyfile(cls.source_file, cls.dest_file)
        
    def setUp(self):
        """
        Creates an subset of the Flask application that loads only the part of the app to be tested.
        """
        self.app = LogAggregator().create_test_app()
        self.app.json_encoder = JSONEncoder
        self.app.config["JWT_SECRET_KEY"] = "iamnotasafekey"
        self.client_app = self.app.test_client()
        self._token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0Mjc4NDQwNywianRpIjoiNDM0ZmY1ZDgtNTk3NS00YzkyLWEyMTctZjE3ZDExN2JjYTg4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImFkbWluIiwibmJmIjoxNzQyNzg0NDA3LCJleHAiOjE3NDI3ODUzMDd9.gXuZp5PG-\_rtN8WKfghXmdh3MFqwbVPB8BY8Rj91ILE"
        self._invalid_token = "iaminvalidtoken"
        self._admin_credentials = {
            "username": "admin",
            "password": "changeme"
        }
        with self.app.app_context():
            User.create_admin()
        self._COMMON_USERNAME = 'johndoe'
        self._COMMON_USERNAME_PASSWORD = 'mypass'
        
    def tearDown(self):
        db.end_db(self.app)
        
    @classmethod
    def tearDownClass(cls):
        """
        Remove the config file created in setUpClass
        """
        if os.path.exists(cls.dest_file):
            os.remove(cls.dest_file)
    
    def test_expired_token(self):
        """
        Test to guarantee that an expired token does not authenticate the user
        """
        auth_headers = {
            "Authorization" : f"Bearer {self._token}"
        }
        body = {
            "username" : "lorem",
            "password" : "ipsum"
        }
        resp = self.client_app.post("/auth/register", 
                             headers=auth_headers, 
                             data=body
                            )
        self.assertEqual(resp.status_code, Constants.HTTP_UNAUTHORIZED.value)

    def test_wrong_password_does_not_authenticate(self):
        """
        Test to guarantee that a wrong password does not authenticate the user
        """
        username = self._admin_credentials["username"]
        password = "wrongpass"
        auth_pass = "{}:{}".format(username, password)
        auth = {
            "Authorization" : "Basic {}".format(base64.b64encode(auth_pass.encode("utf-8")))
        }
        response = self.client_app.get("/auth/login",
                              headers=auth,
                             )
        self.assertEqual(response.status_code, Constants.HTTP_UNAUTHORIZED.value)
    
    def _create_fake_user(self):
        username = self._admin_credentials["username"]
        password = self._admin_credentials["password"]
        auth_pass = "{}:{}".format(username, password)
        auth = {
            "Authorization" : "Basic {}".format(str(base64.b64encode(auth_pass.encode("utf-8")).decode("utf-8")))
        }
        response = self.client_app.get("/auth/login",
                              headers=auth,
                             ).get_json()
        token_auth = {
            "Authorization" : "Bearer {}".format(response['token']['access'])
        }
        body = {
            "username" : self._COMMON_USERNAME,
            "password" : self._COMMON_USERNAME_PASSWORD
        }
        return self.client_app.post("/auth/register",
                             headers=token_auth,
                             json=body)
    
    def test_authorized_token_creates_user(self):
        """
        Test scenario to confirm that a user with admin privileges can create a new user
        """
        response = self._create_fake_user()
        self.assertEqual(response.status_code, Constants.HTTP_CREATED.value)
        
    def test_unauthorized_user_dont_create_user(self):
        """
        Confirms that a user without being an admin cannot create any users
        """
        self._create_fake_user()
        normal_user = {
            "username" : self._COMMON_USERNAME,
            "password" : self._COMMON_USERNAME_PASSWORD
        }
        auth_pass = "{}:{}".format(normal_user["username"], normal_user["password"])
        auth = {
            "Authorization" : f"Basic {str(base64.b64encode(auth_pass.encode("utf-8")).decode("utf-8"))}"
        }
        response = self.client_app.get("/auth/login",
                              headers=auth,
                             ).get_json()
        token_auth = {
            "Authorization" : f"Bearer {response['token']['access']}"
        }
        body = {
            "username" : self._COMMON_USERNAME + 'other',
            "password" : self._COMMON_USERNAME_PASSWORD + 'other'
        }
        response = self.client_app.post("/auth/register",
                             headers=token_auth,
                             json=body)
        self.assertEqual(response.status_code, Constants.HTTP_UNAUTHORIZED.value)
