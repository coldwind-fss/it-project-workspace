from pydantic import BaseModel,ConfigDict
from itpm.core.stage2_responses import AttachmentRow

class PocWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    recordType:str|None=None
    title:str|None=None
    status:str|None=None
    conclusion:str|None=None
    ownerUserId:str|None=None
    ownerName:str|None=None
    projectId:str|None=None
    projectName:str|None=None
    requirementId:str|None=None
    requirementTitle:str|None=None
    demandId:str|None=None
    demandTitle:str|None=None
    sourceType:str|None=None
    sourceRef:str|None=None
    derivedFromId:str|None=None
    objective:str|None=None
    hypothesis:str|None=None
    scope:str|None=None
    sampleData:str|None=None
    method:str|None=None
    successCriteria:str|None=None
    result:str|None=None
    limitations:str|None=None
    nextSteps:str|None=None
    modelName:str|None=None
    modelVersion:str|None=None
    promptOrApproach:str|None=None
    metrics:dict|str|None=None
    reuseGuidance:str|None=None
    tags:list|str|None=None
    artifactType:str|None=None

class PocView(PocWrite):
    id:str
    metrics:dict
    tags:list
    sourceId:str|None=None
    recordTypeLabel:str
    statusLabel:str
    conclusionLabel:str
    sourceLabel:str
    readOnly:bool
    legacy:bool
    createdByUserId:str|None=None
    createdByName:str|None=None
    createdAt:str|None=None
    updatedAt:str|None=None
    completedAt:str|None=None
    archivedAt:str|None=None
    attachments:list[AttachmentRow]

class DeriveWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    title:str|None=None
    reuseGuidance:str|None=None

class PocOptions(BaseModel):
    recordTypes:list[dict[str,str]]
    statuses:list[dict[str,str]]
    conclusions:list[dict[str,str]]
    artifactTypes:list[dict[str,str]]
