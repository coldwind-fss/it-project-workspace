# Explicit physical-field response DTOs, derived once from adopted catalog.
from pydantic import BaseModel,ConfigDict
class ResponseDTO(BaseModel):
    model_config=ConfigDict(extra="allow",strict=True)

class CategoryRow(ResponseDTO):
    id: str | None = None
    name: str | None = None
    icon: str | None = None
    description: str | None = None
    createdAt: str | None = None
    owner: list | str | None = None
    sortOrder: int | None = None
    color: str | None = None
    status: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    deletedAt: str | None = None
    deletedByUserId: str | None = None
    deletedByName: str | None = None

class ProjectRow(ResponseDTO):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    department: str | None = None
    businessOwner: str | None = None
    devOwner: str | None = None
    currentVersion: str | None = None
    startDate: str | None = None
    targetEndDate: str | None = None
    categoryId: str | None = None
    images: list | str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    deletedAt: str | None = None
    deletedByUserId: str | None = None
    deletedByName: str | None = None
    solutionType: str | None = None
    lifecycleTemplate: str | None = None
    complexityLevel: str | None = None

class RequirementRow(ResponseDTO):
    id: str | None = None
    title: str | None = None
    type: str | None = None
    priority: str | None = None
    status: str | None = None
    projectId: str | None = None
    projectName: str | None = None
    sprintId: str | None = None
    assignee: str | None = None
    requester: str | None = None
    description: str | None = None
    acceptanceCriteria: str | None = None
    storyPoints: int | None = None
    labels: str | None = None
    images: list | str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    expectedDeliveryTime: str | None = None
    department: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    completedAt: str | None = None
    deletedAt: str | None = None
    deletedByUserId: str | None = None
    deletedByName: str | None = None
    priorityEvaluation: dict | str | None = None
    changeObject: str | None = None
    impactLevel: str | None = None
    workloadLevel: str | None = None
    itemKind: str | None = None
    parentRequirementId: str | None = None
    versionTarget: str | None = None
    demandId: str | None = None
    flowMode: str | None = None
    lifecycleVersion: int | None = None
    reportingEligible: int | bool | None = None
    registeredAt: str | None = None
    relatedRequirementId: str | None = None

class PhaseRow(ResponseDTO):
    id: str | None = None
    requirementId: str | None = None
    phaseKey: str | None = None
    phaseLabel: str | None = None
    description: str | None = None
    status: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None
    required: int | bool | None = None
    sortOrder: int | None = None
    plannedAt: str | None = None
    startedAt: str | None = None
    completedAt: str | None = None
    evidence: dict | str | None = None
    note: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None

class WorkLogRow(ResponseDTO):
    id: str | None = None
    requirementId: str | None = None
    logType: str | None = None
    content: str | None = None
    operatorUserId: str | None = None
    operatorName: str | None = None
    createdAt: str | None = None
    occurredAt: str | None = None
    sourceBatchId: str | None = None
    workDate: str | None = None
    visibility: str | None = None
    sourceType: str | None = None
    sourceRef: str | None = None
    reportingEligible: int | bool | None = None
    updatedAt: str | None = None

class SprintRow(ResponseDTO):
    id: str | None = None
    name: str | None = None
    projectId: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    status: str | None = None
    releaseNotes: str | None = None
    totalTasks: int | None = None
    completedTasks: int | None = None

class ReleaseRow(ResponseDTO):
    id: str | None = None
    projectId: str | None = None
    version: str | None = None
    releaseDate: str | None = None
    summary: str | None = None
    type: str | None = None

class ChangelogRow(ResponseDTO):
    id: str | None = None
    requirementId: str | None = None
    requirementTitle: str | None = None
    changeType: str | None = None
    fieldName: str | None = None
    oldValue: str | None = None
    newValue: str | None = None
    reason: str | None = None
    operator: str | None = None
    createdAt: str | None = None

class OperationRow(ResponseDTO):
    id: str | None = None
    entityType: str | None = None
    entityId: str | None = None
    entityName: str | None = None
    action: str | None = None
    operator: str | None = None
    operatorRole: str | None = None
    summary: str | None = None
    beforeValue: str | None = None
    afterValue: str | None = None
    createdAt: str | None = None
    sourceBatchId: str | None = None

class AppLogRow(ResponseDTO):
    id: str | None = None
    level: str | None = None
    source: str | None = None
    message: str | None = None
    detail: str | None = None
    path: str | None = None
    userAgent: str | None = None
    userName: str | None = None
    createdAt: str | None = None

class UserRow(ResponseDTO):
    id: str | None = None
    dingUserId: str | None = None
    name: str | None = None
    mobile: str | None = None
    avatar: str | None = None
    title: str | None = None
    department: str | None = None
    role: str | None = None
    devOwnerName: str | None = None
    raw: str | None = None
    lastLoginAt: str | None = None

class Ok(ResponseDTO):
    ok:int
class NamedId(ResponseDTO):
    id:str
    name:str | None = None
    title:str | None = None
class Identifier(ResponseDTO):
    id:str
class BulkResult(Ok):
    deleted:list[str] | None=None
    updated:list[str] | None=None
    skipped:list[dict]
class ProjectCreated(NamedId):
    solutionType:str
    solutionTypeLabel:str
    initialRequirementId:str
class DingConfig(ResponseDTO):
    corpId:str
    agentId:str
    configured:bool
class LoginResult(ResponseDTO):
    user:UserRow
    developers:list[dict]
