import json 
from json import JSONDecodeError


class ConfigManager:
    """
    Class to manage the configuration read from config.json, which will be available system-wide.
    """
    
    _instance = None
    
    def __new__(cls, cfg_file: str):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, cfg_file: str):
        self._cfg_file = cfg_file
        self._config = None
        self._load_config()
        
    def _load_config(self):
        content = ""
        try:
            with open(self._cfg_file, "rt") as fp:
                content = "".join(fp.readlines())
        except FileNotFoundError as e:
            print("Error reading config file: {}".format(e.strerror))
            raise e
        except JSONDecodeError as e:
            print("Error upon parsing JSON file {}: {}", self._cfg_file, e.msg)
            raise e
        self._config = json.loads(content)
    
    @property
    def config(self):
        return self._config
