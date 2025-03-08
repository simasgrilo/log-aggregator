import sqlite3
from pathlib import Path

class FileReaderControl:
    """
    This class controls the file sync process with elasticsearch. It uses a sqlite3 database to keep track of the files that were already read.
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(FileReaderControl, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._conn = sqlite3.connect(Path(__file__).parent.parent.parent.joinpath("db/file_sync.db").__str__(), check_same_thread=False)
        self._cursor = self._conn.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS files (file_name TEXT NOT NULL, timestamp DATETIME not null)")
        
    def add_file(self, file_name: str, timestamp: str):
        """
        Adds a file that was successfully indexed in elasticsearch to the database.
        Args:
            file_name (str): name of the log file processed
            timestamp (str): date of the file processing
        """
        try:
            self._cursor.execute("INSERT INTO files (file_name, timestamp) VALUES (?, ?)", file_name, timestamp)
            self._conn.commit()
        except Exception:
            import traceback
            traceback.print_exc()
    
    def check_if_read(self, file: str):
        """
        Selects the current entry from the control table. if there's a file with the same ID, then it will be ignored by the FileReader.
        Args:
            file_name (str): name of the log file processed
        """
        try:
            self._cursor.execute("SELECT file_name FROM files where file_name = ?", (file,))
            entry = self._cursor.fetchone()
            return entry != None
        except Exception:
            import traceback
            traceback.print_exc()
        return True