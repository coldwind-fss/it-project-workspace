from pydantic import BaseModel,ConfigDict

class SyncLogWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    type:str|None=None
    logType:str|None=None
    content:str|None=None
    occurredAt:str|None=None
class SyncRecordWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    title:str|None=None
    kind:str|None=None
    workKind:str|None=None
    itemKind:str|None=None
    type:str|None=None
    phase:str|None=None
    status:str|None=None
    priority:str|None=None
    impactLevel:str|None=None
    impact:str|None=None
    workloadLevel:str|None=None
    effort:str|None=None
    changeObject:str|None=None
    workDate:str|None=None
    occurredAt:str|None=None
    expectedDeliveryTime:str|None=None
    developerOwner:str|None=None
    assignee:str|None=None
    businessOwner:str|None=None
    requester:str|None=None
    department:str|None=None
    summary:str|None=None
    description:str|None=None
    acceptance:str|None=None
    acceptanceCriteria:str|None=None
    labels:list[str]|str|None=None
    logs:list[SyncLogWrite]|None=None
    workLogs:list[SyncLogWrite]|None=None
    storyPoints:int|str|None=None
    parentRequirementId:str|None=None
    versionTarget:str|None=None
    phaseTemplateKeys:list[str]|None=None
    writeMode:str|None=None
    action:str|None=None
    sourceRefs:list[str]|None=None
class SyncSource(BaseModel):
    model_config=ConfigDict(extra='allow')
    type:str|None=None
    ref:str|None=None
    threadId:str|None=None
    rangeStart:str|None=None
    rangeEnd:str|None=None
    startDate:str|None=None
    endDate:str|None=None

class SyncWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    mode:str|None=None
    projectId:str|None=None
    projectName:str|None=None
    project:dict[str,str]|None=None
    records:list[SyncRecordWrite]|None=None
    idempotencyKey:str|None=None
    source:SyncSource|None=None
    sourceType:str|None=None
    sourceRef:str|None=None
    sourceRangeStart:str|None=None
    sourceRangeEnd:str|None=None
    notify:bool|None=None
class OwnerCorrection(BaseModel):
    model_config=ConfigDict(extra='allow')
    requirementIds:list[str]|None=None
    developerOwner:str|None=None
    businessOwner:str|None=None
    assignee:str|None=None
    requester:str|None=None
    projectId:str|None=None
    reason:str|None=None
class SyncItem(BaseModel):
    model_config=ConfigDict(extra='allow')
    index:int|None=None
    action:str
    title:str
    requirementId:str|None=None
    existingRequirementId:str|None=None
    logsAdded:int|None=None
    link:str|None=None
    reason:str|None=None
    mapped:dict|None=None
    id:str|None=None
    itemIndex:int|None=None
    recordKind:str|None=None
    createdAt:str|None=None
class SyncResult(BaseModel):
    model_config=ConfigDict(extra='allow')
    status:str
    batchId:str
    idempotencyKey:str|None=None
    source:dict[str,str]|None=None
    project:dict[str,str]|None=None
    summary:dict[str,int]|None=None
    items:list[SyncItem]|None=None
    createdAt:str|None=None
    completedAt:str|None=None
    rolledBackAt:str|None=None
    removedRequirements:int|None=None
    removedLogs:int|None=None
class OwnerResult(BaseModel):
    status:str
    developerOwner:str
    businessOwner:str
    updatedRequirementIds:list[str]
    unchangedRequirementIds:list[str]
    auditCreatorUnchanged:bool
class IntakeSchema(BaseModel):
    adapter:str
    projectEntity:str
    workEntity:str
    activityEntity:str
    requiredWorkFields:list[str]
    serviceRequiredWorkFields:list[str]
    fields:dict[str,list[str]]
    canonicalKinds:list[str]
    canonicalPhases:list[str]
    authentication:dict
