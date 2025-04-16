"""Unit test file for main logging functionalities"""
import unittest
from unittest.mock import patch
import os
import sys
import base64
import shutil
from pathlib import Path
from test.test_app_factory import TestAppFactory


sys.path.insert(0, os.path.join(os.path.abspath(Path(__file__).parent.parent.parent), "src"))
sys.path.insert(0, os.path.join(os.path.abspath(Path(__file__).parent.parent.parent)))

class test_log_message(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.source_file = os.path.join(os.path.abspath(Path(__file__).parent.parent), "config.json")
        cls.dest_file = os.path.join(os.path.abspath(Path(__file__).parent.parent.parent), "config.json")
        shutil.copyfile(cls.source_file, cls.dest_file)
    
    def setUp(self):
        self.test_factory = TestAppFactory()
        self.app = self.test_factory.get_test_app()
        self.client_app = self.app.test_client()
        self._COMMON_USERNAME = 'johndoe'
        self._COMMON_USERNAME_PASSWORD = 'mypass'
        
    def tearDown(self):
        self.test_factory.destroy_test_app()
        
    
    @patch("src.Logger.Logger.Logger.flush")
    @patch("src.FileTransferManager.ElasticConnector.ElasticConnector.create_document")
    def test_single_message_sent(self, flush_mock, create_document_mock):
        """
        Test that a single message can be received by the LogAggregator accordingly.
        """
        username, password = self._COMMON_USERNAME, self._COMMON_USERNAME_PASSWORD
        auth_pass = f"{username}:{password}"
        auth = {
            "Authorization" : f"Basic ${str(base64.b64encode(auth_pass.encode("utf-8")).decode("utf-8"))}"
        }
        response = self.client_app.get("/auth/login", headers=auth,).get_json()
        token_auth = {
            "Authorization" : f"Bearer {response['token']['access']}",
        }
        #mock the method that generate the file name and the document creation.
        flush_mock.return_value = "test.log"
        create_document_mock.return_value = "test.log"
        # sample payload as a single string with rows split by newlines
        payload_data = """2025-03-15 01:56:59,303 - 127.0.0.1  - 4109 - INFO - get_dns - server.py - Querying DNS server for address www.yoursite.com"\n
                          2025-03-15 01:58:29,388 - 127.0.0.1  - 4160 - ERROR - get_dns - server.py - Bad request: www.yoursite.com does not exist"""
        response = self.client_app.post("/log", data=payload_data, headers=token_auth)
        self.assertEqual(response.status_code, 200)