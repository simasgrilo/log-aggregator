"""Class to log messages from different sources into a cloud solution"""
from src.LogEntry.LogEntry import LogEntry
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
from pydantic import ValidationError
import json
from datetime import datetime, timezone
from botocore import exceptions

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
            f.write(log_entry)
            self._sequential_id += 1
        try:
            self._file_transfer_manager.transfer_file(self._dir + file_name, self._config.config["S3"]["bucketName"], file_name)
        except exceptions.ClientError as e:
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()       
            
    def log(self, header, payload: bytes):
        payload = self.__parse(header, payload)
        # log_entry = LogEntry(\
        #     application_server_ip=header.remote_addr, \
        #     application_id=payload["application_id"], \
        #     date=payload["date"], \
        #     time=payload["time"], \
        #     client_ip=payload["client_ip"], \
        #     level= payload["level"] if "level" in payload else "", \
        #     method= payload["http_method"] if "http_method" in payload else "", \
        #     component= payload["component"] if "component" in payload else "", \
        #     message= payload["message"] if "message" in payload else "" \
        # )
        self.flush(payload)

    def __parse(self, header, message: bytes):
        """
        Args:
            message (bytes): message to be parsed into a dictionary
        """
        parsed_message = []
        message = str(message, encoding='utf-8').split("\n")
        try:
            for log_row in message:
                if not log_row:
                    break
                log_row = log_row.split("-")
                year, month = log_row[0:2]
                day, time = log_row[2].split(" ")[:-1]
                date = "{}-{}-{}".format(year, month, day)
                #remove any extra blank spaces that parts of the message can have:
                log_row = [row.strip(" ") for row in log_row]
                parsed_message.append(
                    LogEntry(
                        application_server_ip=header.remote_addr,
                        application_id=log_row[4],
                        date=date,
                        time=time,
                        client_ip=log_row[3],
                        level=log_row[5],
                        method=log_row[6],
                        component=log_row[7],
                        message=log_row[8]
                    ).__str__()
                )
        except ValueError as e:
            return "Error when parsing message {} : {}".format(log_row, e.msg)
        except ValidationError as e:
            return e.json()
        return json.dumps(parsed_message)
    
    
    def get_logs(self):
        return self._logs