from flask import Flask, request
from src.Logger.Logger import Logger
from src.FileTransferManager.FileUploader import FileUploader
from json import JSONDecodeError


class LogAggregator:
    
    def __init__(self):
        self.__log = Logger("C:\\Next level\\PSP - Yuri\\100 Days\\LogAggregator\\static\\", FileUploader().get_instance())
        self.app = Flask(__name__)
        self.app.add_url_rule("/", "online", self.online)
        self.app.add_url_rule("/log", "log", self.log, methods=["POST"])

    def run(self):
        self.app.run(port=8080)
    
    def online(self):
        return "<h1> LogAggregator is online </h1>"
    
    def log(self):
        """Method to log messages from different sources. The full structure of the logging messages is defined in class Logger.py
            this method logs the message using the Logger definition, returning to the client the origin IP of the logged message.s
        Returns:
            None
        """        
        try:
            self.__log.log(request, request.data)
            return "Log received from {}".format(request.remote_addr), 200  # OK
        except JSONDecodeError as e:
            return "Invalid JSON: {}".format(e.msg), 400
        except FileNotFoundError and OSError as e:
            return "Error writing log to file {}: ".format(e.filename, e.strerror), 500
        
if __name__ == "__main__":
    log_aggregator = LogAggregator()
    log_aggregator.run()