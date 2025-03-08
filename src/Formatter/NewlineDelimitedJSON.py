from typing import List
import json
from json import JSONDecodeError

class NewlineDelimitedJSON:
    """
    Class to provide a functionality to format the logs in a newline delimited JSON format. Its primary use is to allow making bulk requests to Elasticsearch with
    the logs data
    """
    
    @staticmethod
    def ndjson(logs: List[str], index: str) -> str:
        """
        Formats the logs in a newline delimited JSON Format

        Args:
            logs (List[str]): data from logs to be formatted

        Returns:
            str: a string containing the log formated where each pair of rows contain the action to be bulk processed in Elasticsearch and the document.
            Example:
            {"index": {"_index": "<indexname>"}} \n
            {"field1": "data1", "field2": "data2"}} \n
            {"index": {"_index": "<indexname>"}\n
            {"field2": {"data3"}, ...} \n
        """
        payload = []
        for log_entry in logs:
            row = "{{\"index\": {{\"_index\": \"{}\"}}}}\n".format(index)
            try:
                jsonified_log = json.loads(log_entry)
            #TODO decide what to do if the log is not a valid JSON. Either continue with the processing or raise an exception
            except JSONDecodeError:
                continue
                #raise JSONDecodeError("Invalid JSON: {}".format(log_entry), log_entry)
            row += log_entry + '\n'
            payload.append(row)
        return "".join(payload)