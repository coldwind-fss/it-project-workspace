from pydantic import BaseModel, ConfigDict

class Command(BaseModel):
    model_config=ConfigDict(extra="allow")

class DemandCreate(Command):
    title: str | None = None
    description: str | None = None
    problemAndOutcome: str | None = None
    originalFeedback: str | None = None
    content: str | None = None
    requesterName: str | None = None
    requesterUserId: str | None = None
    projectId: str | None = None
    department: str | None = None
    intakeLevel: str | None = None
    businessPriority: str | None = None
    businessUrgency: str | None = None
    expectedDeliveryTime: str | None = None
    sourceType: str | None = None
    sourceRef: str | None = None
    recipientToken: str | None = None

class DemandEvaluation(Command):
    status: str | None = None
    evaluationDecision: str | None = None
    evaluationReason: str | None = None
    evaluationNotes: str | None = None
    requestType: str | None = None
    solutionType: str | None = None
    intakePath: str | None = None
    aiMode: str | None = None
    aiScenario: str | None = None
    pocRequirement: str | None = None
    impactScope: str | None = None
    complexityLevel: str | None = None
    completeness: str | None = None
    similarDemandId: str | None = None
    nextAction: str | None = None
    answers: dict | str | None = None

class DemandDecomposition(Command):
    mode: str | None = None
    branches: list | None = None
    requireMultiple: bool | None = None

class DemandConversion(Command):
    mode: str | None = None
    projectId: str | None = None
    requirementId: str | None = None
    parallelL3s: list | None = None
    units: list | None = None
    title: str | None = None
    itemKind: str | None = None
    projectName: str | None = None
    department: str | None = None
    devOwner: str | None = None
    projectOwner: str | None = None
    projectEndDate: str | None = None
    solutionType: str | None = None
    priority: str | None = None
    categoryId: str | None = None
    phaseTemplateKeys: list | None = None
    acceptanceCriteria: str | None = None
    assignee: str | None = None
    expectedDeliveryTime: str | None = None
    type: str | None = None
    changeObject: str | None = None
    impactLevel: str | None = None
    workloadLevel: str | None = None
    versionTarget: str | None = None
    storyPoints: int | str | None = None
    labels: str | None = None

class BranchDecisions(Command):
    decisions: list | None = None

class ReviewAssignment(Command):
    reviewers: list | None = None

class ReviewReuse(Command):
    contactName: str | None = None
    contactUserId: str | None = None
    communicationDate: str | None = None
    source: str | None = None
    decision: str | None = None
    prioritySuggestion: str | None = None
    summary: str | None = None

class ReviewSubmission(Command):
    token: str | None = None
    decision: str | None = None
    valueAssessment: str | None = None
    prioritySuggestion: str | None = None
    expectedOutcome: str | None = None
    riskNotes: str | None = None
    comment: str | None = None
    branchDecisions: list | None = None

class ConfirmationCreate(Command):
    recipientUserId: str | None = None
    recipientName: str | None = None
    templateType: str | None = None
    content: dict | None = None
    usageScope: str | None = None
    businessProcess: str | None = None
    acceptanceCriteria: str | None = None

class ConfirmationSubmission(Command):
    token: str | None = None
    decision: str | None = None
    confirmationComment: str | None = None

class SupplementCreate(Command):
    solutionType: str | None = None
    questions: list | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None

class SupplementSubmission(Command):
    answers: dict | str | None = None

class MaterialsSubmission(Command):
    recipientToken: str | None = None
    token: str | None = None
    demandId: str | None = None
    additionalInfo: str | None = None
    description: str | None = None
    hasAttachments: bool | None = None

class PoolPocCreate(Command):
    summary: str | None = None
    result: str | None = None
    artifactText: str | None = None
    goal: str | None = None
    successCriteria: str | None = None
    ownerName: str | None = None
    ownerUserId: str | None = None
    dueDate: str | None = None
    baseline: dict | str | None = None
    scope: str | None = None
    testData: str | None = None
    artifactType: str | None = None
    aiUsed: str | None = None
    aiNotes: str | None = None

class PoolPocUpdate(Command):
    status: str | None = None
    result: str | None = None
    conclusion: str | None = None

