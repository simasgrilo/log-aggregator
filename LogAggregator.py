""" Main module of the LogAggregator solution, in which the Flask app is initialized, along with other required dependencies.
    For more details, please refer to the documentation at https://www.github.com/simasgrilo/LogAggregator.
"""
import os
import sys
import inspect
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from src.Logger.Logger import Logger
from src.database import DB as db
from src.auth import auth_bp, LogJWTManager as jwt
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
from src.FileTransferManager.ElasticConnector import ElasticConnector
from src.blueprints import LogBlueprint
from src.docs.py.docs import doc_app
#from src.blueprints.docs import LogDoc
#from src.blueprints.docs.auth_doc import api as auth_namespace


class LogAggregator:
    
    app = None
    
    def __init__(self,
                 config_path ="./config.json",
                 test_config = None,
                 logger_instance = None,
                 uploader = None,
                 elastic_connector = None,
                 ):
        try:
            self.__config = ConfigManager(config_path)
            file_uploader = uploader or FileUploader().get_instance()
            elastic_connector = elastic_connector or ElasticConnector(self.__config).get_instance()
            self.__log = logger_instance or Logger(file_uploader, self.__config, elastic_connector)
            self.app = Flask(__name__)
            self.app.json_encoder = json.JSONEncoder
            #self.app.config.from_prefixed_env()
            #initialize the database:
            if test_config:
                self.app.config.update(test_config)
            else:
                load_dotenv()
                db_dir = os.path.join(f"sqlite:///{os.path.abspath(Path(__file__).parent)}","database","log_aggregator.db")
                self.app.config.from_prefixed_env()
                self.app.config["SQLALCHEMY_DATABASE_URI"] =  db_dir
            db.initialize_db(self.app)
            jwt.initialize_manager(self.app)
            # register the log blueprint
            log_bp = LogBlueprint.create_log_blueprint(self.__log)
            self.app.register_blueprint(log_bp,url_prefix='/')
            # register the blueprints for authentication: every authentication related resource needs to be prefixed with /auth
            self.app.register_blueprint(auth_bp,url_prefix='/auth')
            # Swagger UI implementation in a separate blueprint
            self.app.register_blueprint(doc_app, url_prefix='/api')
        except FileNotFoundError as exc:
            message = inspect.cleandoc("""Missing config.json file. Please provide a valid file when starting the app. 
                     If this app was started using Docker, please ensure that your Docker run has a -v volume binding that maps the config.json file 
                     to ./config.json""")
            sys.stderr.write(message)
            raise FileNotFoundError("Shutting down. No config.json found") from exc
        
    def run(self):
        self.app.run(port=8080)
        
    def get_logger(self):
        return self.__log

