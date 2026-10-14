from pydantic import BaseModel,ConfigDict,field_validator

class BulkIds(BaseModel):
    model_config=ConfigDict(extra='allow')
    ids:list[str]|None=None
    @field_validator('ids',mode='before')
    @classmethod
    def legacy_ids(cls,value):return [str(x) for x in value if x] if isinstance(value,list) else value
