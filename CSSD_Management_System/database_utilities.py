import sqlalchemy as sql
import os 
mapping_datatype = {'string' : sql.String , 'float' : sql.Float , 'integer' : sql.Integer , 'boolean' : sql.Boolean}

class DATABASE:
    def __init__(self , database_name = "mydb.db"):
        self.database_name = database_name
        self.database_path = os.path.join(os.getcwd() , "app" , database_name)
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

            column_obj = sql.Column(column_name , 
                                    mapping_datatype[datatype] , 
                                    nullable = nullable , 
                                    primary_key = primary_key)

            final_columns.append(column_obj)

        return final_columns
    
    

    def create_table(self, table_name , columns_dict):
        columns_objs = self.__dict_to_columns(columns_dict)

        table = sql.Table(table_name , self.metadata , *columns_objs)

        self.metadata.create_all(self.engine)


database = DATABASE()

database.create_table('table' , {'test' : {'nullable' : False , 'primary_key' : True , 'datatype' : 'string'}})