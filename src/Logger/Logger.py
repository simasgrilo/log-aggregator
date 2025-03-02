"""Class to log messages from different sources into a cloud solution"""
from src.LogEntry.LogEntry import LogEntry
from src.FileTransferManager.FileTransferManager import FileTransferManager
import json


class Logger:
    
    def __init__(self, dir: str, file_transfer_manager: FileTransferManager):
        self._dir = dir
        self._file_transfer_manager = file_transfer_manager
        self._logs = []
    
    def flush(self, log_entry: LogEntry):
        #TODO: note that relying on the timestamp coming from a single node in a distributed environemnt can introduce some sort of incosistency.
        #maybe this is a nice use case for logical clocks (Lamport?)
        file_name = "log_file_{}_{}_{}{}".format(log_entry.application_server_ip, log_entry.application_id, log_entry.timestamp.replace(":","-"), ".log")
        # try:
        with open(self._dir + file_name, "wt") as f:
            f.write(log_entry.__str__())
        try:
            #TODO parametrize bucket name in a config file
            self._file_transfer_manager.transfer_file(self._dir + file_name, "simasgrilo-log-aggregator", file_name)
        except Exception as e:
            import traceback
            traceback.print_exc()       
            
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
        self.flush(log_entry)

    def __parse(self, message: bytes):
        """
        Args:
            message (bytes): message to be parsed into a dictionary
        """
        parsed_message = ""
        for char in message:
            parsed_message += chr(char)
        return json.loads(parsed_message)
    
    
    def get_logs(self):
        return self._logs