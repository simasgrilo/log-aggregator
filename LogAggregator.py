from flask import Flask, request
from src.Logger.Logger import Logger
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
from src.FileTransferManager.ElasticConnector import ElasticConnector
from src.FileTransferManager.FileReader import FileReader
from src.FileTransferManager.FileReaderControl import FileReaderControl
from pydantic import ValidationError
import json
from json import JSONDecodeError


class LogAggregator:
    
    def __init__(self):
        self.__config = ConfigManager("C:\\Next level\\PSP - Yuri\\100 Days\\LogAggregator\\config.json")
        self.__log = Logger("C:\\Next level\\PSP - Yuri\\100 Days\\LogAggregator\\static\\", FileUploader().get_instance(), self.__config)
        self.app = Flask(__name__)
        self.app.add_url_rule("/", "online", self.online)
        self.app.add_url_rule("/log", "log", self.log, methods=["POST"])

    def run(self):
        self.app.run(port=8080)
    
    def online(self):
        return "<h1> LogAggregator is online </h1>"
    
    def log(self):
        """Method to log messages from different sources. The full structure of the logging messages is defined in class Logger.py
            this method logs the message using the Logger definition, returning to the client the origin IP of the logged messages.
            This endpoint will be used by the clients to send their logs to the aggregator. It will reunite these in files and then send it to Elasticsearch instance.
        Returns:
            None
        """        
        try: 
            self.__log.log(request, request.data)
            return "Log received from {}".format(request.remote_addr), 200  # OK
        except JSONDecodeError as e:
            return "Invalid JSON: {}".format(e.msg), 400
        except FileNotFoundError and OSError:
            return "Error writing log to file {}: ".format(e.filename, e.strerror), 500
        except ValidationError as e:
            error_msg = {
                "Error" : "Invalid log entry",
                "Details" : e.errors()
            }
            return json.dumps(error_msg), 500
        
if __name__ == "__main__":
    log_aggregator = LogAggregator()
    log_aggregator.run()