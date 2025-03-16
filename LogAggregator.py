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
import sys
import inspect

class LogAggregator:
    
    def __init__(self):
        try:
            self.__config = ConfigManager("./config.json") 
            self.__log = Logger("./static", 
                                FileUploader().get_instance(), 
                                self.__config,
                                ElasticConnector(self.__config).get_instance())
            self.app = Flask(__name__)
            self.app.add_url_rule("/", "online", self.online)
            self.app.add_url_rule("/log", "log", self.log, methods=["POST"])
        except FileNotFoundError:
            message = inspect.cleandoc("""Missing config.json file. Please provide a valid file when starting the app. 
                     If this app was started using Docker, please ensure that your Docker run has a -v volume binding that maps the config.json file 
                     to ./config.json""")
            sys.stderr.write(message)
            sys.exit(1)
            #raise FileNotFoundError("Shutting down. No config.json found")

    def app(self):
        return self.app

    def run(self):
        self.app.run(port=8080)
    
    def online(self):
        return "<h1> LogAggregator is online </h1>"
    
    def log(self):
        """Method to log messages from different sources. The full structure of the logging messages is defined in class Logger.py
            this method logs the message using the Logger definition, returning to the client the origin IP of the logged messages.
            This endpoint will be used by the clients to send their logs to the aggregator. It will reunite these in files and then send it to Elasticsearch instance.
        Returns
            None
        """        
        try: 
            self.__log.log(request, request.data)
            return "Log received from {}".format(request.remote_addr), Constants.HTTP_OK.value  # O
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
        
app = LogAggregator().app
app.run()