"""Class to log messages from different sources into a cloud solution"""
from src.LogEntry.LogEntry import LogEntry
import sys
import json


class Logger:
    
    def __init__(self):
        self.logs = []
    

    def log(self, header, payload: bytes):
        #try:
            # log_entry = {
            #     "application_server_ip": header.remote_addr,
            #     "application_id": payload["application_id"], 
            #     "client_ip": payload["client_ip"],
            #     "http_method": payload["http_method"] if payload["http_method"] else "",
            #     "resource_requested": payload["resource_requested"] if payload["resource_requested"] else "",
            #     "protocol": payload["protocol"] if payload["protocol"] else "",
            #     "status_code": payload["status_code"] if payload["status_code"] else "",
            #     "message": payload["status_code"] if payload["status_code"] else "",
            #     "level": payload["level"] if payload["level"] else ""   
            # }
        payload = self.__parse(payload)
        log_entry = LogEntry( \
            application_server_ip=header.remote_addr, \
            application_id=payload["application_id"], \
            timestamp=payload["timestamp"], \
            client_ip=payload["client_ip"], \
            http_method= payload["http_method"] if "http_method" in payload else "", \
            resource_requested= payload["resource_requested"] if "resource_requested" in payload else "", \
            protocol= payload["protocol"] if "protocol" in payload else "", \
            status_code= payload["status_code"] if "status_code" in payload else "", \
            message= payload["message"] if "message" in payload else "", \
            level= payload["level"] if "level" in payload else "" \
        )
        self.logs.append(log_entry)
        # except ValueError:            
        #     import traceback
        #     traceback.print_exc()   
    
    def __parse(self, message: bytes):
        """
        Args:s
            message (bytes): message to be parsed into a dictionary
        """
        parsed_message = ""
        for char in message:
            parsed_message += chr(char)
        return json.loads(parsed_message)
    
    
    def getLogs(self):
        return self.logs