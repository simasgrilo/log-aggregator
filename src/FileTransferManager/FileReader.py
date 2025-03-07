import boto3
from src.FileTransferManager.Reader import Reader
from src.FileTransferManager.FileReaderControl import FileReaderControl
from src.ConfigManager.ConfigManager import ConfigManager

class FileReader(Reader):
    """
    Reads file from S3 repository, returning the content as a parsed string. This content will be sent to the elasticsearch instance for indexing.
    Considering S3 as the source of truth of the logging system, this class will read the files from the S3 repository and return their content as documents
    to be indexed in the elasticsearch instance (only new files). 
    """
    _instance = None
    
    def __new__(cls, config_manager: ConfigManager, file_reader_control: FileReaderControl):
        if not cls._instance:
            cls._instance = super(FileReader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_manager: ConfigManager, file_reader_control: FileReaderControl):
        self._config_manager = config_manager
        self._file_reader_control = file_reader_control
        self._bucket_name = self._config_manager.config["S3"]["bucketName"]
        self._s3 = boto3.client('s3')
    
    def read(self):
        """
        Reads the file from the S3 repository and returns the content as a string.
        If the file was already processed, it will be ignored and the processing begins from the next file in the bucket.
        """
        try:
            bucket_content = self._s3.list_objects(Bucket=self._bucket_name)
            if bucket_content["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise Exception("Error reading bucket content {}".format(bucket_content["Contents"]))
            contents = []
            for file in bucket_content["Contents"]:
                file_processed = self._file_reader_control.check_if_read(file["Key"]) #this needs to be close to the document creation... or the document check needs to be added here.
                if file_processed:
                    continue
                data = self._s3.get_object(Bucket=self._bucket_name, Key=file["Key"])
                if data["ResponseMetadata"]["HTTPStatusCode"] != 200:
                    raise Exception("Error reading file {}".format(file["Key"]))
                read_data = data["Body"].read().decode("utf-8") 
                contents.append(read_data)
            return contents
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None 