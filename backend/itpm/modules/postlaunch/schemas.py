from pydantic import BaseModel, ConfigDict

class Command(BaseModel):
    model_config=ConfigDict(extra="allow")

class PostlaunchWrite(Command):
    targetType: str | None = None
    targetId: str | None = None
    requirementId: str | None = None
    projectId: str | None = None
    deliveryKind: str | None = None
    deliveryDate: str | None = None
    deliveryRoundId: str | None = None
    plannedDeliveryDate: str | None = None
    useStartDate: str | None = None
    businessOwnerName: str | None = None
    businessOwnerUserId: str | None = None
    status: str | None = None
    notes: str | None = None

class PostlaunchIssueWrite(Command):
    operationId: str | None = None
    title: str | None = None
    severity: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    description: str | None = None
    ownerName: str | None = None
    ownerUserId: str | None = None
    dueDate: str | None = None
    discoveredAt: str | None = None
    status: str | None = None
    resolution: str | None = None
    rootCause: str | None = None
    prevention: str | None = None

class PostlaunchProposalWrite(Command):
    operationId: str | None = None
    title: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    problem: str | None = None
    suggestion: str | None = None
    expectedChange: str | None = None
    status: str | None = None
    linkedRequirementId: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None

class PostlaunchKnowledgeWrite(Command):
    operationId: str | None = None
    title: str | None = None
    content: str | None = None
    artifactType: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    status: str | None = None

