from pydantic import BaseModel, field_validator
from typing_extensions import Annotated
from enum import Enum

class LogLevel(str, Enum):
    INFO = 'INFO'
    WARN = 'WARNING',
    ERROR = 'ERROR',
    CRITICAL = 'CRITICAL',
    DEBUG = 'DEBUG'

class LogEntry(BaseModel):
    application_server_ip : Annotated[str, 'check_application_server_ip'] #IP of the server where the logged service is running
    application_id: int #ID of the application that is logging the message
    date: Annotated[str, 'timestamp_not_empty'] #date of the log occurence
    time: Annotated[str, 'timestamp_not_empty'] #time of the log occurence
    client_ip: Annotated[str, 'check_application_server_ip'] #client IP that requested the resource when the log entry was produced
    level: LogLevel #level of criticality of the log entry
    method: str #method of component that was called when the message was logged
    component: str #module/class that contains the method that was called when the message was logged
    message: str #additional information being logged     level: str  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL' #level of criticality of the log entry

    def to_json(self):
        return {
            "application_server_ip": self.application_server_ip,
            "application_id": self.application_id,
            "date": self.date,
            "time": self.time,
            "client_ip": self.client_ip,
            "level": self.level,
            "method": self.method,
            "component": self.component,
            "message": self.message
        }

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