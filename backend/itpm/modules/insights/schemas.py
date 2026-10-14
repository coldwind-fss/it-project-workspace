from pydantic import BaseModel,ConfigDict
from itpm.core.responses import RequirementRow,ProjectRow,ChangelogRow,CategoryRow

class View(BaseModel):model_config=ConfigDict(extra='allow')
class DashboardStats(View):
    activeProjects:int
    monthlyNewRequirements:int
    pendingBugs:int
    monthlyReleases:int
class CategorySummary(CategoryRow):
    reqCount:int
    doneCount:int
    projectCount:int
class CategoryWork(RequirementRow):
    pname:str|None=None
    categoryId:str|None=None
    cname:str|None=None
class DashboardActivityView(ChangelogRow):
    type:str|None=None
    status:str|None=None
    priority:str|None=None
    assignee:str|None=None
    requester:str|None=None
    reqDepartment:str|None=None
    projectName:str|None=None
    projectId:str|None=None
    projectDepartment:str|None=None
    projectStatus:str|None=None
    categoryId:str|None=None
    cname:str|None=None
class ReportItem(View):
    kind:str
    title:str
    status:str
    text:str
class ReportGroup(View):
    projectName:str
    items:list[ReportItem]
class ProjectChange(View):
    id:str
    name:str
    oldStatus:str
    newStatus:str
    text:str
    createdAt:str
class WorkReport(View):
    period:str
    title:str
    rangeLabel:str
    generatedAt:str
    newProjects:list[ProjectRow]
    projectChanges:list[ProjectChange]
    groups:list[ReportGroup]
    summary:dict[str,int]
    markdown:str
class Score(View):
    value:float|None
    max:float
    autoValue:float|None
    autoMax:float
    basis:str
class Completion(View):
    status:str
    summary:str
    facts:list[dict]
    gaps:list[str]
    evidenceIds:list[str]
class PerformanceRow(View):
    index:int
    key:str
    indicator:str
    scoringRule:dict
    dataSources:list[dict]
    completion:Completion
    score:Score
    weight:float
class PerformanceDraft(View):
    month:str
    userName:str
    ruleVersion:str
    generatedAt:str
    counts:dict[str,int]
    summary:dict[str,float|int|None]
    rows:list[PerformanceRow]
    evidence:dict[str,list[dict]]
class PerformanceRecord(View):
    id:str
    userId:str
    month:str
    goals:str
    plan:str
    nextPlan:str
    draft:PerformanceDraft|str
    finalText:str
    status:str
    createdAt:str
    updatedAt:str
    finalizedAt:str
class PerformanceResult(View):
    record:PerformanceRecord|None
    draft:PerformanceDraft
class PerformanceWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    month:str|None=None
    goals:str|None=None
    plan:str|None=None
    nextPlan:str|None=None
    finalText:str|None=None
    final:bool|None=None
