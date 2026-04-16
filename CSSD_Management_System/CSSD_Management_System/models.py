import datetime 
import time
from enum import Enum

ts = time.time()

class State(Enum):
    Unassigned = 'Unassigned'
    Requested = 'Requested'
    Collected = 'Collected'
    Cleaned = 'Cleaned'
    Sterilized = 'Sterilized'
    Packed = 'Packed'
    Delivered = 'Delivered'



# Models

class User:
    def __init__(self , id , email , hashed_password , role , departement):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.role = role
        self.department = departement
        self.created_at = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

class InstrumentSet:
    def __init__(self , id , name, type , quantitiy  , created_at , updated_at):
        self.id = id
        self.name = name 
        self.type = type
        self.quantity = quantitiy
        self.state = State('Unassigned')
        self.created_at = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.updated_at = self.created_at


class Sterilization_Batch:
    def __init__(self , id , operator_id , temperature , cycle_duration , status = 'In Progress' , created_at = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')):
        self.id = id
        self.operator_id = operator_id
        self.temperature = temperature
        self.cycle_duration = cycle_duration
        self.status = status


