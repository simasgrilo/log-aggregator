
from flask import Blueprint
from src.services.log_service import LogService


class LogBlueprint():
    
    @staticmethod
    def create_log_blueprint(logger):
        """
        Creates the log functionality blueprint. This is the main functionality that calls the remainder of the methods to push to S3 and Elasticsearch
        Args:
            logger (src.Logger.Logger): An instance of a Logger object, which defines the logging utility (process, parse, send to S3, etc).
            This should be the LogAggregator's log instance as this blueprint will be registered in the LogAggregator class.

        Returns:
            log_bp (Blueprint): the log blueprint to be used in the LogAggregator construction.
        """
        log_bp = Blueprint("log", __name__, url_prefix="/")
        
        @log_bp.get("/")
        def online():
            return LogService.online()
        
        @log_bp.post("/log")
        def log():
            return LogService.log(logger)
            
        return log_bp