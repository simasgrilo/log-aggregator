"""
Swagger UI documentation for log services related operation. This is essentially the same endpoints
as the ones defined in the log blueprint
Returns:
    _type_: _description_
"""
from flask_restx import Namespace, fields, Resource
from src.services.log_service import LogService

_api = Namespace("log", description="Log related operations")

@_api.route('/') #note: the path /docs/log is defined in LogAggregator file upon registering the namespace with the Flask app.
class LogDoc(Resource):
    
    log_model = _api.model("Log", {
            "message": fields.String(required=True, description="The log message"),
    })
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
       
    @_api.marshal_with(log_model, skip_none=True)
    @_api.expect(log_model, validate=False)
    @_api.doc(security='jwt', response={200: "Succes", 
                                        400: "Bad Request", 
                                        403: "Forbidden", 
                                        500: "Internal Server Error"
                                        })
    def post(self):
        """
        Documentation of the main endpoint used for logging messages.
        The string must be in NDJSON format, where each row is a JSON Object denoting the log occurrence.
        """
        return LogService.log(self.logger)
    
    @staticmethod
    def get_api():
        """
        Returns the API namespace for log operations.
        """
        return _api