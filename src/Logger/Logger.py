"""Class to log messages from different sources into a cloud solution"""
from src.LogEntry.LogEntry import LogEntry
from src.FileTransferManager.FileUploader import FileUploader
from src.ConfigManager.ConfigManager import ConfigManager
from src.FileTransferManager.ElasticConnector import ElasticConnector
from datetime import datetime, timezone
from botocore import exceptions
import json
import os
from pathlib import Path

class Logger:
    
    def __init__(self, file_transfer_manager: FileUploader, config: ConfigManager, elastic_connector: ElasticConnector):
        self._file_transfer_manager = file_transfer_manager
        self._elastic_connector = elastic_connector
        self._config = config
        #date will be logged in UTC for all logs to avoid timezone inconsistencies.
        self._start_date = datetime.now(timezone.utc)
        #autoincrement ID to denote the i'th logfile of the day
        self._sequential_id = 1
            
    def log(self, header, payload: bytes):
        """
        Method to generate the log file and send it to the corresponding S3 bucket. If successful, the file is deleted from the server.
        Otherwise it is stored in a queue for processing later.
        Args:
            header (flask.Request): Flask header of the request that was received by LogAggregatror
            payload (bytes): Payload of the logged file to be pushed to S3
        """
        parsed_payload = self.__parse(header, payload)
        file_name = self.flush(parsed_payload)
        self._delete_file(file_name)
        self._elastic_connector.create_document(file_name, parsed_payload)
        # except exceptions.ClientError as e:
        #   pass
        # except Exception as e:
        #     import traceback
        #     traceback.print_exc()
        #     raise Exception(e.args)

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
                    ).model_dump_json() + '\n'
                )
        except ValueError as e:
            raise ValueError("Error when parsing message {} : {}".format(log_row, e))
        # except ValidationError as e:
        #     e.add_note(e.json)
        #     raise ValidationError.add_note(e.json())
        return parsed_message

    def flush(self, log_entry: LogEntry):
        """
        Flushes the file to a temporary log file with name considering the current timestamp and how many files were created with this timestamp

        Args:
            log_entry (LogEntry): _description_
        """
        log_creation_date = datetime.now(timezone.utc)
        date = log_creation_date.strftime("%Y-%m-%d")
        time = log_creation_date.strftime("%H:%M:%S")
        if self._start_date.strftime("%Y-%m-%d") != date:
            #different date as of previous logs: reset id and date
            self._start_date = date
            self._sequential_id = 1
        file_name = "logaggregator_{}_{}.log".format(date, self._sequential_id)
        log_files_path = os.path.join(Path(__file__).parent.parent, self._config.config["logs"]["path"], file_name)
        while os.path.isfile(Path(__file__).parent.parent.parent.joinpath("{}{}".format(log_files_path,file_name))):
            self._sequential_id += 1
            file_name = "logaggregator_{}_{}.log".format(date, self._sequential_id)
        # try:
        with open(log_files_path, "wt") as f:
            f.writelines(log_entry)
            self._sequential_id += 1
        self._file_transfer_manager.transfer_file(log_files_path, self._config.config["S3"]["bucketName"], file_name)
        return file_name
    
    def _delete_file(self, file_name: str):
        try:
            os.remove(file_name)
        except FileNotFoundError as e:
            return "File {} not found to be removed. Perhaps it was moved?".format(e.filename)
