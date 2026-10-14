from pydantic import BaseModel,ConfigDict
from itpm.infrastructure.stage2_contracts import PostlaunchView

class DashboardMetric(BaseModel):
    key:str
    label:str
    value:float|None
    numerator:int
    denominator:int
    coverage:float|None
    period:str
    operationIds:list[str]
    note:str
class OperationalWork(BaseModel):
    id:str
    operationId:str
    title:str
    deliveryDate:str
    plannedDeliveryDate:str
    lifecycleStage:str
    acceptanceOutcome:str
    valueVerificationStatus:str
    dataStatus:str
    lifecycleProgress:int
    openIssueCount:int
    day7Status:str
    day7SubmittedAt:str
    day30Status:str
    day30SubmittedAt:str
class OperationalProduct(BaseModel):
    key:str
    projectId:str
    name:str
    projectType:str
    department:str
    businessPriority:str
    businessPriorityLabel:str
    operations:int
    l3Rows:list[OperationalWork]
    l3Count:int
    latestAt:str
    valueVerificationStatus:str
    lifecycleStage:str
class PostlaunchDashboard(BaseModel):
    summary:dict[str,int]
    metrics:list[DashboardMetric]
    l2Rows:list[OperationalProduct]
    rows:list[PostlaunchView]
    generatedAt:str
    excludedOperations:int
    filters:dict[str,str]
