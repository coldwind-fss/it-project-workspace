from pydantic import BaseModel,ConfigDict
class LogWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    level:str|None=None
    source:str|None=None
    message:str|None=None
    detail:str|None=None
    path:str|None=None
    userAgent:str|None=None
    userName:str|None=None
