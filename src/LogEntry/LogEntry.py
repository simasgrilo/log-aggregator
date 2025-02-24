from pydantic import BaseModel, field_validator
from typing_extensions import Annotated

class LogEntry(BaseModel):
    application_server_ip : Annotated[str, 'check_application_server_ip'] #IP of the server where the logged service is running
    application_id: str #ID of the application that is logging the message
    timestamp: Annotated[int, 'timestamp_not_empty'] #timestamp of the log occurence
    client_ip: Annotated[str, 'check_application_server_ip'] #client IP that requested the resource when the log entry was produced
    http_method: str #Method of the client IP call that requested the resource when the log entry was produced
    resource_requested: str #resource requested in the server that is creating the log entry
    protocol: str #protocol used in the request that generated the log entry
    status_code: int #optional: if the log entry is created within a response process of the server, then it can log the status code the server is returning to the client
    message: str #additional information being logged 
    level: str  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL' #level of criticality of the log entry


    def check_application_server_ip(self, value):
        #TODO add validator for IPv6 address
        """
        Args:
            value (str): IPv4 from the server where the application is running

        Raises:
            ValueError: _description_
        """        
        if not value:
            raise ValueError('application_server_ip cannot be empty')
        if not self.__valid_ip(value):
            raise ValueError('application_server_ip is not a valid IP address')
        
    def __valid_ip(self, value):
        """
        Args:
            value (str): IPv4 from the server where the application is running

        Returns:
            isValid (boolean): whether the current IP is a valid IPv4 address
        """
        value = value.split(".")
        if len(value) != 4:
            return False
        for octet in value:
            if int(octet) < 0 or int(octet) > 255:
                return False 
        return True
        
    def timestamp_not_empty(self, timestamp):
        if not timestamp:
            raise ValueError('timestamp cannot be empty')