"""Class to log messages from different sources into a cloud solution"""
from src.LogEntry.LogEntry import LogEntry
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
import json
from datetime import datetime, timezone


class Logger:
    
    def __init__(self, dir: str, file_transfer_manager: FileUploader, config: ConfigManager):
        self._dir = dir
        self._file_transfer_manager = file_transfer_manager
        self._config = config
        self._logs = []
        #date will be logged in UTC for all logs to avoid timezone inconsistencies.
        self._start_date = datetime.now(timezone.utc)
        #autoincrement ID to denote the i'th logfile of the day
        self._sequential_id = 1
    
    def flush(self, log_entry: LogEntry):
        """
        Flushes the file to a temporary log file with name considering the current timestamp and how many files were created with this timestamp

        Args:
            log_entry (LogEntry): _description_
        """
        log_creation_date = datetime.now(timezone.utc)
        date = log_creation_date.strftime("%Y-%m-%d")
        time = log_creation_date.strftime("%H:%M:%S")
        file_name = None
        if self._start_date.strftime("%Y-%m-%d") != date:
            #different date as of previous logs: reset id and date
            self._start_date = date
            self._sequential_id = 1
        file_name = "logaggregator_{}_{}.log".format(date, self._sequential_id)
        # try:
        with open(self._dir + file_name, "wt") as f:
            f.write(json.dumps(log_entry.to_json()))
            self._sequential_id += 1
        try:
            self._file_transfer_manager.transfer_file(self._dir + file_name, self._config.config["S3"]["bucketName"], file_name)
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
        log_entry = LogEntry(\
            application_server_ip=header.remote_addr, \
            application_id=payload["application_id"], \
            date=payload["date"], \
            time=payload["time"], \
            client_ip=payload["client_ip"], \
            level= payload["level"] if "level" in payload else "", \
            method= payload["http_method"] if "http_method" in payload else "", \
            component= payload["component"] if "component" in payload else "", \
            message= payload["message"] if "message" in payload else "" \
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