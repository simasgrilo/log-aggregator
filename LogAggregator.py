from flask import Flask, request
from src.Logger.Logger import Logger



class LogAggregator:
    
    def __init__(self):
        self.__log = Logger()
        self.app = Flask(__name__)
        self.app.add_url_rule("/", "online", self.online)
        self.app.add_url_rule("/log", "log", self.log, methods=["POST"])

    def run(self):
        self.app.run(port=8080)
    
    def online(self):
        return "<h1> LogAggregator is online </h1>"
    
    def log(self):
        """Method to log messages from different sources. It needs to process both the IP and the body of the services that are sending logs

        Returns:
            None
        """        
        self.__log.log(request, request.json)
        return "Log received from {}".format(request), 200  # OK
        
if __name__ == "__main__":
    log_aggregator = LogAggregator()
    log_aggregator.run()