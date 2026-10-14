from pydantic import BaseModel,ConfigDict
from itpm.core.schemas import BulkIds

class CategoryWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    name:str|None=None
    icon:str|None=None
    description:str|None=None
    owner:list|None=None
    sortOrder:int|None=None
    color:str|None=None
    status:str|None=None

class ProjectWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    name:str|None=None
    description:str|None=None
    status:str|None=None
    solutionType:str|None=None
    lifecycleTemplate:str|None=None
    complexityLevel:str|None=None
    priority:str|None=None
    department:str|None=None
    businessOwner:str|None=None
    devOwner:str|None=None
    currentVersion:str|None=None
    startDate:str|None=None
    targetEndDate:str|None=None
    categoryId:str|None=None
    images:list|str|None=None
    createInitialL3:bool|None=None
    phaseTemplateKeys:list[str]|None=None

