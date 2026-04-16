import sqlalchemy as sql
import os 
mapping_datatype = {'string' : sql.String , 'float' : sql.Float , 'integer' : sql.Integer , 'boolean' : sql.Boolean}
database_path = os.path.join(os.path.dirname(__file__)  , 'db.sqlite3')


class DATABASE:
    def __init__(self , database_path  , database_name = "db.sqlite3"):
        self.database_name = database_name
        self.database_path = database_path
        self.database_url = f"sqlite:///{database_name}"
        self.engine = sql.create_engine(self.database_url)
        self.cursor = self.engine.connect()
        self.metadata = sql.MetaData()

    def execute_query(self , query : str):
        """
        write SQL Query in text to be executed
        
        """
        query_in_text = sql.text(query)

        result = self.cursor.execute(query_in_text)

        return result.fetchall()
    
    def __dict_to_columns(self , columns_dict):
        final_columns = []
        for column in columns_dict:
            column_name = column
            metadata = columns_dict[column]
            nullable = metadata['nullable']
            primary_key = metadata['primary_key']
            datatype = metadata['datatype']
            server_default = metadata['server_default']
            if server_default is None:
                column_obj = sql.Column(column_name , 
                                    mapping_datatype[datatype] , 
                                    nullable = nullable , 
                                    primary_key = primary_key)
            else:
                column_obj = sql.Column(column_name , 
                                    mapping_datatype[datatype] , 
                                    nullable = nullable , 
                                    primary_key = primary_key , server_default = server_default)


            final_columns.append(column_obj)

        return final_columns
    
    

    def create_table(self, table_name , columns_dict):
        """
        columns_dict : {column_name : {datatype : ... , nullable : ... , primary_key : ...}}        
        """

        columns_objs = self.__dict_to_columns(columns_dict)

        table = sql.Table(table_name , self.metadata , *columns_objs)

        self.metadata.create_all(self.engine)


    def drop_table(self , tablename):
        drop_query = sql.text(f"DROP TABLE IF EXISTS {tablename};")

        self.cursor.execute(drop_query)

    
    def get_connection(self):
        return self.engine
    
    def get_tables(self):
        return self.metadata.tables


