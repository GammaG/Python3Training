import mysql.connector
from main.ConnectionException import ConnectionException


class DatabaseConnection:

    def __init__(self, config):
        self.config = config

    def __enter__(self) -> 'cursor':
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor()
            return self.cursor
        except Exception as err:
            raise ConnectionException(err)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
