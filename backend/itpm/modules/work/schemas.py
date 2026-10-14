from pydantic import BaseModel,ConfigDict,field_validator

class Classification(BaseModel):
    model_config=ConfigDict(extra='allow')
    type:str|None=None
    status:str|None=None
    changeObject:str|None=None
    impactLevel:str|None=None
    workloadLevel:str|None=None
    reason:str|None=None
    @field_validator('type','status','changeObject','impactLevel','workloadLevel',mode='before')
    @classmethod
    def legacy_classification(cls,value):return str(value) if value is not None and not isinstance(value,str) else value

class RequirementWrite(Classification):
    title:str|None=None
    priority:str|None=None
    itemKind:str|None=None
    parentRequirementId:str|None=None
    demandId:str|None=None
    flowMode:str|None=None
    reportingEligible:bool|int|None=None
    relatedRequirementId:str|None=None
    versionTarget:str|None=None
    projectId:str|None=None
    sprintId:str|None=None
    assignee:str|None=None
    requester:str|None=None
    department:str|None=None
    description:str|None=None
    acceptanceCriteria:str|None=None
    expectedDeliveryTime:str|None=None
    storyPoints:int|float|None=None
    labels:str|None=None
    priorityEvaluation:dict|str|list|None=None
    images:list|str|None=None
    phaseTemplateKeys:list[str]|None=None

class BulkClassification(Classification):
    ids:list[str]|None=None

class WorkLogWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    content:str|None=None
    logType:str|None=None
    workDate:str|None=None
    visibility:str|None=None
    sourceType:str|None=None
    sourceRef:str|None=None

class PhaseWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    phaseKey:str|None=None
    phaseLabel:str|None=None
    title:str|None=None
    description:str|None=None
    status:str|None=None
    ownerUserId:str|None=None
    ownerName:str|None=None
    required:bool|int|None=None
    sortOrder:int|None=None
    plannedAt:str|None=None
    evidence:dict|str|None=None
    note:str|None=None

class SprintWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    name:str|None=None
    projectId:str|None=None
    startDate:str|None=None
    endDate:str|None=None
    status:str|None=None
    releaseNotes:str|None=None

class ReleaseWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    projectId:str|None=None
    version:str|None=None
    releaseDate:str|None=None
    summary:list|None=None
    type:str|None=None
