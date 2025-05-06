import boto3
from botocore.exceptions import NoCredentialsError



class FileUploader:
    """
    Class to manage file transfer between server and cloud storage using AWS S3. The objective is to store all collected logs in buckets in AWS so tehy will be acessed by ElasticSearch
    """    
    
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(FileUploader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._s3_client = boto3.client('s3')
    
    
    def get_instance(cls):
        return cls._instance
    
    def transfer_file(self, file_path, bucket_name, object_name):
        """
        Transfer a file to a bucket in AWS S3
        :param: file_path: str: path of file to be transfered
        :param: bucket_name: str: name of the bucket in S3
        :param: object_name: str: name of the object in the bucket (defaults to the file name if not specified)
        """
        try:
            self._s3_client.upload_file(file_path, bucket_name, object_name)
            print("File transfered successfully")
        except FileNotFoundError:
            print("The file was not found")
        except NoCredentialsError:
            print("Credentials not available")
        except Exception as e:
            print(f"An error occurred: {e}")