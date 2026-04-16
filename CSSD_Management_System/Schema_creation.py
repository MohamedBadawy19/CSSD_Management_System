from database_utilities import DATABASE , database_path 
from sqlalchemy import func
database = DATABASE(database_path = database_path , database_name = "db.sqlite3")

User_Schema ={
   'id': {"datatype" : "string" , 'nullable' : False , 'primary_key' : True , 'server_default' : None},
    'email' : {'datatype' : 'string' , 'nullable' : False , 'primary_key' :False , 'server_default' : None},
    'hashed_password' : {"datatype" : "string" , 'nullable' : False , 'primary_key' : False , 'server_default' : None},
    'role' : {"datatype" : "string" , 'nullable' : False , 'primary_key' : False , 'server_default' : None},
    'department' : {"datatype" : "string" , 'nullable' : False , 'primary_key' : False , 'server_default' : None},
    'created_At' : {"datatype" : "string" , 'nullable' : False , 'primary_key' : False , 'server_default' : func.now()}
}
InstrumentSet_Schema = {
    'id' : {"datatype" : "string" , 'nullable' : False , 'primary_key' : True , 'server_default' : None},
    'name': {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'type' : {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'quantity': {'datatype' : "integer" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'state' : {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'created_at': {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : func.now()},
    'updated_at' :  {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : func.now()}

}


Sterilization_Batch_Schema = {
    'id' : {"datatype" : "string" , 'nullable' : False , 'primary_key' : True , 'server_default' : None},
    'operator_id': {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'temperature' : {'datatype' : "float" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'cycle_duration': {'datatype' : "float" , "nullable" : False , "primary_key" : False , "server_default" : None} ,
    'status' : {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : 'In Progress'} ,
    'created_at': {'datatype' : "string" , "nullable" : False , "primary_key" : False , "server_default" : func.now()},
    
}


database.create_table('User' , User_Schema)
database.create_table('InstrumentSet' , InstrumentSet_Schema)
database.create_table('Sterilization_Batch' , Sterilization_Batch_Schema)