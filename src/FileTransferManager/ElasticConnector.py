import requests
from src.FileTransferManager.Reader import Reader
from src.Formatter.NewlineDelimitedJSON import NewlineDelimitedJSON
from typing import List

class ElasticConnector:
    """
    Class to connect the read files from S3 to the corresponding Elasticsearch instance
    It implements a fraction of the logstash functionalities restricted to file reading. The indexing nomenclature simulates
    Logstash default index naming convention.
    Process:
    
    Indexes are created per each file read from AWS. The index name is composed by the prefix "logaggregator-" followed by the date of the file creation.
    
    """
    
    def __init__(self, elastic_config: dict):
        """
        Creates a new instance of a connector to the Elasticsearch instance.
        Variable elastic_config will hold the references read from the config file to connect to Elasticsearch
        Args:
            elastic_config (dict): Dictionary containing the configuration read from the config file to connect to Elasticsearch
        """
        if not elastic_config:
            raise Exception("Elasticsearch config not provided. Please check your config.json file.")
        self._config = elastic_config

    def create_document(self, index_name:str, content: List[str]):
        """
        Creates a document in the Elasticsearch instance from the file read. A new index is only created if an index for the current file does not exist.
        """
        index_exists = self.retrieve_index(index_name)
        if not index_exists:
            self.create_index(index_name)
        ndjson = NewlineDelimitedJSON.ndjson(content, index_name)
        auth = (self._config["auth"]["username"], self._config["auth"]["password"])
        bulk_url = "https://{}:{}".format(self._config["host"], self._config["port"])+ "/" + index_name + "/_bulk"
        headers = {
            "Content-Type" : "application/x-ndjson"
        }
        req = requests.post(url=bulk_url, auth=auth, headers=headers, data=ndjson, verify=False)
        if req.status_code != 200:
            raise Exception("Error upon creating bulk request for index {}: message {}".format(index_name, req.json()))
        return req.json()

    def create_index(self, index_name: str):
        """
        Creates an index in the Elasticsearch instance based on the amount of files that were created in this day.
        """
        index_url = "https://{}:{}/{}".format(self._config["host"], self._config["port"], index_name)
        auth = (self._config["auth"]["username"], self._config["auth"]["password"])
        req = requests.put(url=index_url, auth=auth, verify=False)
        if req.status_code != 200:
            raise Exception("Error upon requesting index {}: message {}".format(index_name, req.json()))
    
    def retrieve_index(self, index_name: str):
        """
        Retrieves the index from the Elasticsearch instance based on the file name
        """
        url = "https://{}:{}".format(self._config["host"], self._config["port"]) + self._config["endpoints"]["indexQuery"].format(index_name)
        #this endpoint does not default its return type to application/json.
        headers = {
            "Accept" : "application/json"
        } 
        auth_config = (self._config["auth"]["username"], self._config["auth"]["password"])
        req = requests.get(url=url ,auth=auth_config, headers=headers, verify=False)

        if req.status_code == 404:
            return None
        if req.status_code == 200:
            return req.json()
        if req.status_code % 100 == 4 or req.status_code % 100 == 5:    
            raise Exception("Error upon requesting index {}: message {}".format(index_name, req.json()["error"]))
