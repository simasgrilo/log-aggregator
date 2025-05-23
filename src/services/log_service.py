import json
from json import JSONDecodeError
from flask_jwt_extended import jwt_required, get_jwt, exceptions
from pydantic import ValidationError
from flask import request
from src.Utils import Constants

class LogService:
    """
    Logging service logic to be called in the blueprints definition. This is decoupled from the Blueprint as the need to
    document the APIs with Swagger had been identified, and Flask-RESTX was chosen for that. As Flask-RESTX uses Namespaces
    (quite similar to Blueprints), the logic was decoupled from the blueprint definition to avoid duplication in both
    Blueprint and Namespaces
    """
    
    @staticmethod
    def online():
        return "<h1> LogAggregator is online </h1>"
    
    @staticmethod
    @jwt_required()
    def log(logger):
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
            logger.log(request, request.data)
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
        