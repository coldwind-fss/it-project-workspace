from pydantic import BaseModel,ConfigDict

class LoginWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    authCode:str|None=None
    code:str|None=None

class Assignment(BaseModel):
    model_config=ConfigDict(extra='allow')
    name:str|None=None
    userId:str|None=None
    accessRole:str|None=None
    isDeveloper:bool|None=None
    enabled:bool|None=None

class CustomRole(BaseModel):
    model_config=ConfigDict(extra='allow')
    key:str|None=None
    label:str|None=None
    description:str|None=None
    pages:list[str]=[]
    actions:list[str]=[]

class TodoPolicy(BaseModel):
    skipSelfAssignedTodo:bool=False
    notifyRequesterOnOnline:bool=True

class PersonnelWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    assignments:list[Assignment]|None=None
    customRoles:list[CustomRole]|None=None
    todoSettings:TodoPolicy|None=None
