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
from test.test_app_factory import TestAppFactory
from src.Utils import Constants


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
        self.test_factory = TestAppFactory()
        self.app = self.test_factory.get_test_app()
        self.app.config["JWT_SECRET_KEY"] = "iamnotasafekey"
        self.client_app = self.app.test_client()
        self._token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0Mjc4NDQwNywianRpIjoiNDM0ZmY1ZDgtNTk3NS00YzkyLWEyMTctZjE3ZDExN2JjYTg4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImFkbWluIiwibmJmIjoxNzQyNzg0NDA3LCJleHAiOjE3NDI3ODUzMDd9.gXuZp5PG-\_rtN8WKfghXmdh3MFqwbVPB8BY8Rj91ILE"
        self._invalid_token = "iaminvalidtoken"
        self._admin_credentials = {
                "username": "admin",
                "password": "changeme"
        }
        self._common_credentials = {
            "username": "lorem",
            "password": "ipsum"
        }
        
    def tearDown(self):
        self.test_factory.destroy_test_app()
        
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
        response = self._login(username, password)
        self.assertEqual(response.status_code, Constants.HTTP_BAD_REQUEST.value)
        
    def _login(self, username: str, password: str):
        auth_pass = f"{username}:{password}"
        auth = {
            "Authorization" : "Basic {}".format(str(base64.b64encode(auth_pass.encode("utf-8")).decode("utf-8")))
        }
        return self.client_app.get("/auth/login",headers=auth)
    
    def _create_fake_user(self):
        username = self._admin_credentials["username"]
        password = self._admin_credentials["password"]
        response = self._login(username, password).get_json()
        token_auth = {
            "Authorization" : "Bearer {}".format(response['token']['access'])
        }
        body = {
            "username" : self._common_credentials["username"],
            "password" : self._common_credentials["password"]
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
            "username" : self._common_credentials["username"],
            "password" : self._common_credentials["password"]
        }
        response = self._login(normal_user["username"], normal_user["password"]).get_json()
        token_auth = {
            "Authorization" : f"Bearer {response['token']['access']}"
        }
        body = {
            "username" : self._common_credentials["username"] + 'other',
            "password" : self._common_credentials["password"] + 'other'
        }
        response = self.client_app.post("/auth/register",
                             headers=token_auth,
                             json=body)
        self.assertEqual(response.status_code, Constants.HTTP_UNAUTHORIZED.value)
        
    #ERICK - tests for password change request
    def test_change_password(self):
        response = self._create_fake_user()
        username = self._admin_credentials["username"]
        password = self._admin_credentials["password"]
        new_password = "newpassword"
        response = self._login(username, password).get_json()
        token_auth = {
            "Authorization": f"Bearer {response['token']['access']}"
        }
        password_response = self.client_app.post("/auth/changePassword", 
                                                 headers=token_auth,
                                                 json={
                                                     "username" : username,
                                                     "password": new_password
                                                 })
        self.assertEqual(password_response.status_code, Constants.HTTP_OK.value)
        login_new_pass = self._login(username, new_password)
        self.assertEqual(login_new_pass.status_code, Constants.HTTP_OK.value)
        
    def test_delete_user(self):
        """
        Test scenario: user with admin privileges deletes a user. the user to be deleted is OK before deletion, and after deletion the login request should sreturn 400.
        1) create the fake user (which will be deleted)
        2) login with the created user needs to be OK
        3) login with admin user needs to be OK
        4) call the delete user endpoint with the admin credentials for the created user in step 1 must be successful
        5) deleted user can no longer login with the same credentials
        """
        response = self._create_fake_user()
        common_username = self._common_credentials["username"]
        common_password = self._common_credentials["password"]
        logon_response = self._login(common_username, common_password)
        self.assertEqual(logon_response.status_code, Constants.HTTP_OK.value)
        admin_username = self._admin_credentials["username"]
        admim_password = self._admin_credentials["password"]
        response = self._login(admin_username, admim_password).get_json()
        token_auth = {
            "Authorization": f"Bearer {response['token']['access']}"
        }
        delete_response = self.client_app.delete("/auth/deleteUser", 
                                                 headers=token_auth,
                                                 json={
                                                     "username" : self._common_credentials["username"],
                                                     "password": self._common_credentials["password"]
                                                 })
        self.assertEqual(delete_response.status_code, Constants.HTTP_OK.value)
        login_del_user = self._login(self._common_credentials["username"], self._common_credentials["password"])
        self.assertEqual(login_del_user.status_code, Constants.HTTP_BAD_REQUEST.value)
