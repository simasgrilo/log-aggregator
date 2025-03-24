from flask import Flask, request
from src.Logger.Logger import Logger
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
from src.FileTransferManager.ElasticConnector import ElasticConnector
from src.FileTransferManager.FileReader import FileReader
from src.FileTransferManager.FileReaderControl import FileReaderControl
from src.Utils.Constants import Constants
from pydantic import ValidationError
import json
from json import JSONDecodeError
from src.database import DB as db
from src.auth import auth_bp, LogJWTManager as jwt
from pathlib import Path
from flask_jwt_extended import jwt_required
from flask_jwt_extended import exceptions
# from auth2 import auth_bp
import os
import sys
import inspect

class LogAggregator:
    
    app = None
    
    def __init__(self):
        try:
            self.__config = ConfigManager("./config.json") 
            self.__log = Logger("./static", 
                                FileUploader().get_instance(), 
                                self.__config,
                                ElasticConnector(self.__config).get_instance())
            self.app = Flask(__name__)
            self.app.json_encoder = json.JSONEncoder
            #self.app.config.from_prefixed_env()
            #initialize the database:
            db_dir = "sqlite:///{}".format(os.path.abspath(Path(__file__).parent) + "\\database\\log_aggregator.db")
            # XXX those three attributes below must be moved to a .env file to be read by your app and set the Flask object's config.
            # if read automatically from the .env file, they need to be prefixed with FLASK_.
            self.app.config["SQLALCHEMY_DATABASE_URI"] =  db_dir #"sqlite:///mydb.db"
            self.app.config["SECRET_KEY"] = "jQkaiekolfpqjmAFSFASF"
            self.app.config["JWT_SECRET_KEY"] = "24b7f04e775d9725abb1b365"
            db.initialize_db(self.app)
            jwt.initialize_manager(self.app)
            # register the public routes
            self.app.add_url_rule("/", "online", self.online)
            self.app.add_url_rule("/log", "log", self.log_service, methods=["POST"])
            # register the blueprints for authentication: every authentication related resource needs to be prefixed with /auth
            self.app.register_blueprint(auth_bp,url_prefix='/auth')
        except FileNotFoundError:
            message = inspect.cleandoc("""Missing config.json file. Please provide a valid file when starting the app. 
                     If this app was started using Docker, please ensure that your Docker run has a -v volume binding that maps the config.json file 
                     to ./config.json""")
            sys.stderr.write(message)
            raise FileNotFoundError("Shutting down. No config.json found")

    # def app(self):
    #     return self.app

    def run(self):
        self.app.run(port=8080)
    
    def online(self):
        return "<h1> LogAggregator is online </h1>"
    
    #@app.post("/log")
    #this needs to be set BEFORE the register of the handler, of course
    #TODO possible approach: encapsule the handler in a function so the decorator is seen in the register route call when initializign the app
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
                self.__log.log(request, request.data)
                return "Log received from {}".format(request.remote_addr), Constants.HTTP_OK.valuea
            except JSONDecodeError as e:
                return "Invalid JSON: {}, document is {}".format(e.args, e.doc), Constants.HTTP_BAD_REQUEST.value
            except ValueError and IndexError as e:
                return "Error upon parsing input payload. Please refer to the documentation to get the correct expected format".format(e.args), Constants.HTTP_BAD_REQUEST.value
            except FileNotFoundError and OSError as e:
                return "Error writing log to file {}: {}. This is probably due to the Elasticsearch instance being offline. Please contact the system's administrator.".format(e.filename, e.strerror), Constants.HTTP_INTERNAL_SERVER_ERROR.value
            except ValidationError as e:
                error_msg = {
                    "Error" : "Invalid log entry",
                    "Details" : e.errors()
                }
                return json.dumps(error_msg), Constants.HTTP_BAD_REQUEST
            except exceptions.NoAuthorizationError:
                return "Invalid authorization header. Please check your request header Authorization record", Constants.HTTP_BAD_REQUEST.val
        return log(self)
    
app = LogAggregator().app
app.run()