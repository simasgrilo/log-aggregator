""" Main module of the LogAggregator solution, in which the Flask app is initialized, along with other required dependencies.
    For more details, please refer to the documentation at https://www.github.com/simasgrilo/LogAggregator.
"""
import os
import sys
import inspect
import json
from pathlib import Path
from json import JSONDecodeError
from dotenv import load_dotenv
from flask import Flask, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, exceptions, get_jwt
from src.Logger.Logger import Logger
from src.database import DB as db
from src.auth import auth_bp, LogJWTManager as jwt
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
from src.FileTransferManager.ElasticConnector import ElasticConnector
from src.Utils.Constants import Constants


class LogAggregator:
    
    app = None
    
    def __init__(self):
        try:
            self.__config = ConfigManager("./config.json") 
            self.__log = Logger(FileUploader().get_instance(), 
                                self.__config,
                                ElasticConnector(self.__config).get_instance())
            self.app = Flask(__name__)
            self.app.json_encoder = json.JSONEncoder
            #self.app.config.from_prefixed_env()
            #initialize the database:
            db_dir = os.path.join("sqlite:///{}".format(os.path.abspath(Path(__file__).parent)),"database","log_aggregator.db")
            load_dotenv()
            self.app.config.from_prefixed_env()
            self.app.config["SQLALCHEMY_DATABASE_URI"] =  db_dir
            db.initialize_db(self.app)
            jwt.initialize_manager(self.app)
            # register the public routes
            self.app.add_url_rule("/", "online", self.online)
            self.app.add_url_rule("/log", "log", self.log_service, methods=["POST"])
            # register the blueprints for authentication: every authentication related resource needs to be prefixed with /auth
            self.app.register_blueprint(auth_bp,url_prefix='/auth')
        except FileNotFoundError as exc:
            message = inspect.cleandoc("""Missing config.json file. Please provide a valid file when starting the app. 
                     If this app was started using Docker, please ensure that your Docker run has a -v volume binding that maps the config.json file 
                     to ./config.json""")
            sys.stderr.write(message)
            raise FileNotFoundError("Shutting down. No config.json found") from exc
    def run(self):
        self.app.run(port=8080)
    
    def online(self):
        return "<h1> LogAggregator is online </h1>"
    
    #@app.post("/log")
    #this needs to be set BEFORE the register of the handler, of course
    #TODO possible approach: encapsule the handler in a function so the decorator is seen in the register route call when initializing the app
    def log_service(self):
        @jwt_required()
        def log(self):
            """Method to log messages from different sources. The full structure of the logging messages is defined in class Logger.py
                this method logs the message using the Logger definition, returning to the client the origin IP of the logged messages.
                This endpoint will be used by the clients to send their logs to the aggregator. It will reunite these in files and then send it to Elasticsearch instance.
            Returns
                None
            """        
            try:
                claims = get_jwt()
                if "log" not in claims["perm"]:
                    return json.dumps({
                        "error": "missing authorization for requested resource"
                    }), Constants.HTTP_UNAUTHORIZED.value
                self.__log.log(request, request.data)
                return f"Log received from {request.remote_addr}", Constants.HTTP_OK.value
            except JSONDecodeError as e:
                return f"Invalid JSON: {e.args}, document is {e.doc}", Constants.HTTP_BAD_REQUEST.value
            except (ValueError, IndexError) as e:
                return f"Error upon parsing input payload. Please refer to the documentation to get the correct expected format: {e.args}", Constants.HTTP_BAD_REQUEST.value
            except (FileNotFoundError, OSError) as e:
                return f"Error writing log to file {e.filename}: {e.strerror}. This is probably due to the Elasticsearch instance being offline. Please contact the system's administrator.", Constants.HTTP_INTERNAL_SERVER_ERROR.value
            except ValidationError as e:
                error_msg = {
                    "Error" : "Invalid log entry",
                    "Details" : e.errors()
                }
                return json.dumps(error_msg), Constants.HTTP_BAD_REQUEST.value
            except exceptions.NoAuthorizationError:
                return "Invalid authorization header. Please check your request header Authorization record", Constants.HTTP_BAD_REQUEST.value
        return log(self)
    
    def create_test_app(self):
        """
        Creates an subset of the Flask application that loads only the part of the app to be tested.
        """
        app = Flask(__name__)
        app.config.update({
            "TESTING" : True,
            "SQLALCHEMY_DATABASE_URI" : "sqlite:///:memory:"
        })
        app.add_url_rule("/", "online", self.online)
        app.add_url_rule("/log", "log", self.log_service, methods=["POST"])
        app.register_blueprint(auth_bp,url_prefix='/auth')
        db.initialize_db(app)
        jwt.initialize_manager(app)
        return app

app = LogAggregator().app
