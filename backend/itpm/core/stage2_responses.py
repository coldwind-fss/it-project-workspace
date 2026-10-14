from pydantic import BaseModel,ConfigDict
class ResponseDTO(BaseModel):
    model_config=ConfigDict(extra="allow",strict=True)

class DemandRow(ResponseDTO):
    id: str
    title: str | None = None
    description: str | None = None
    requesterUserId: str | None = None
    requesterName: str | None = None
    department: str | None = None
    projectId: str | None = None
    projectName: str | None = None
    expectedDeliveryTime: str | None = None
    businessPriority: str | None = None
    sourceType: str | None = None
    sourceRef: str | None = None
    status: str | None = None
    requestType: str | None = None
    evaluationDecision: str | None = None
    evaluationReason: str | None = None
    evaluationNotes: str | None = None
    evaluationOwnerUserId: str | None = None
    evaluationOwnerName: str | None = None
    evaluatedAt: str | None = None
    confirmedAt: str | None = None
    requirementId: str | None = None
    requirementTitle: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    closedAt: str | None = None
    intakeLevel: str | None = None
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
    deletedAt: str | None = None
    deletedByUserId: str | None = None
    deletedByName: str | None = None

class BranchRow(ResponseDTO):
    id: str
    demandId: str | None = None
    sortOrder: int | bool | None = None
    branchKey: str | None = None
    title: str | None = None
    itemKind: str | None = None
    scope: str | None = None
    difference: str | None = None
    relationToValue: str | None = None
    proposedPriority: str | None = None
    dependency: str | None = None
    businessDecision: str | None = None
    businessPriority: str | None = None
    businessComment: str | None = None
    itDecision: str | None = None
    itReason: str | None = None
    itNotes: str | None = None
    formalRequirementId: str | None = None
    status: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None

class ReviewRow(ResponseDTO):
    id: str
    demandId: str | None = None
    reviewerRole: str | None = None
    reviewerRoleLabel: str | None = None
    reviewerUserId: str | None = None
    reviewerName: str | None = None
    reviewerDepartment: str | None = None
    status: str | None = None
    decision: str | None = None
    valueAssessment: str | None = None
    prioritySuggestion: str | None = None
    expectedOutcome: str | None = None
    riskNotes: str | None = None
    comment: str | None = None
    link: str | None = None
    notificationStatus: str | None = None
    notificationError: str | None = None
    sentAt: str | None = None
    submittedAt: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    token: str | None = None
    branchDecisions: str | dict | list | None = None

class ConfirmationRow(ResponseDTO):
    id: str
    demandId: str | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    status: str | None = None
    businessProcess: str | None = None
    usageScope: str | None = None
    usageFrequency: str | None = None
    acceptanceCriteria: str | None = None
    successMetric: str | None = None
    confirmationComment: str | None = None
    confirmedByUserId: str | None = None
    confirmedByName: str | None = None
    confirmedAt: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    token: str | None = None
    notificationStatus: str | None = None
    notificationError: str | None = None
    sentAt: str | None = None
    templateType: str | None = None
    content: str | dict | list | None = None

class SupplementRow(ResponseDTO):
    id: str
    demandId: str | None = None
    solutionType: str | None = None
    status: str | None = None
    questions: str | list | None = None
    answers: str | dict | list | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    submittedAt: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None

class PoolPocRow(ResponseDTO):
    id: str
    demandId: str | None = None
    status: str | None = None
    goal: str | None = None
    baseline: str | dict | list | None = None
    scope: str | None = None
    testData: str | None = None
    successCriteria: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None
    dueDate: str | None = None
    result: str | None = None
    conclusion: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    completedAt: str | None = None
    artifactType: str | None = None
    aiUsed: str | None = None
    aiNotes: str | None = None

class SharedActivityRow(ResponseDTO):
    id: str
    scopeType: str | None = None
    scopeId: str | None = None
    projectId: str | None = None
    requirementId: str | None = None
    activityType: str | None = None
    title: str | None = None
    content: str | dict | list | None = None
    actorUserId: str | None = None
    actorName: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    deletedAt: str | None = None

class SharedCommentRow(ResponseDTO):
    id: str
    activityId: str | None = None
    projectId: str | None = None
    requirementId: str | None = None
    commenterUserId: str | None = None
    commenterName: str | None = None
    content: str | dict | list | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    deletedAt: str | None = None

class CollaborationRow(ResponseDTO):
    id: str
    requirementId: str | None = None
    businessRequestId: str | None = None
    direction: str | None = None
    kind: str | None = None
    status: str | None = None
    title: str | None = None
    content: str | dict | list | None = None
    requesterUserId: str | None = None
    requesterName: str | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    dueDate: str | None = None
    response: str | None = None
    sourceType: str | None = None
    sourceRef: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    respondedAt: str | None = None
    closedAt: str | None = None

class MessageRow(ResponseDTO):
    id: str
    collaborationId: str | None = None
    requirementId: str | None = None
    senderUserId: str | None = None
    senderName: str | None = None
    senderSide: str | None = None
    messageType: str | None = None
    content: str | dict | list | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    deletedAt: str | None = None

class IntakeRow(ResponseDTO):
    id: str
    kind: str | None = None
    status: str | None = None
    title: str | None = None
    originalFeedback: str | None = None
    requesterUserId: str | None = None
    requesterName: str | None = None
    department: str | None = None
    projectId: str | None = None
    projectName: str | None = None
    requirementId: str | None = None
    requirementTitle: str | None = None
    assignee: str | None = None
    assigneeUserId: str | None = None
    expectedDeliveryTime: str | None = None
    priority: str | None = None
    sourceType: str | None = None
    sourceRef: str | None = None
    handlerNote: str | None = None
    handledByUserId: str | None = None
    handledByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    handledAt: str | None = None
    businessUrgency: str | None = None

class AttachmentRow(ResponseDTO):
    id: str
    ownerType: str | None = None
    ownerId: str | None = None
    originalName: str | None = None
    storedName: str | None = None
    mimeType: str | None = None
    fileExtension: str | None = None
    sizeBytes: int | bool | None = None
    sha256: str | None = None
    storageKey: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    deletedAt: str | None = None

class TodoRow(ResponseDTO):
    id: str
    recipientUserId: str | None = None
    recipientName: str | None = None
    requirementId: str | None = None
    requirementTitle: str | None = None
    projectId: str | None = None
    projectName: str | None = None
    sourceUserId: str | None = None
    sourceName: str | None = None
    type: str | None = None
    status: str | None = None
    message: str | None = None
    dingTalkSent: int | bool | None = None
    createdAt: str | None = None
    readAt: str | None = None
    doneAt: str | None = None
    dingTalkTaskId: str | None = None
    dingTalkUnionId: str | None = None
    dingTalkError: str | None = None
    businessCollaborationId: str | None = None

class BaselineRow(ResponseDTO):
    id: str
    requirementId: str | None = None
    version: int | bool | None = None
    templateType: str | None = None
    content: str | dict | list | None = None
    status: str | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    confirmationLinkId: str | None = None
    supersedesId: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    confirmedAt: str | None = None
    sourceDemandConfirmationId: str | None = None

class LinkRow(ResponseDTO):
    id: str
    requirementId: str | None = None
    collaborationId: str | None = None
    requestMessageId: str | None = None
    kind: str | None = None
    token: str | None = None
    clientKey: str | None = None
    snapshot: str | dict | list | None = None
    status: str | None = None
    expiresAt: str | None = None
    responseMessageId: str | None = None
    outcome: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    submittedAt: str | None = None
    revokedAt: str | None = None

class FeedbackRow(ResponseDTO):
    id: str
    requirementId: str | None = None
    deliveryRoundId: str | None = None
    baselineId: str | None = None
    feedbackType: str | None = None
    routeType: str | None = None
    content: str | dict | list | None = None
    requestedTitle: str | None = None
    routedRequirementId: str | None = None
    status: str | None = None
    submittedByUserId: str | None = None
    submittedByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    resolvedAt: str | None = None

class ValueCardRow(ResponseDTO):
    id: str
    demandId: str | None = None
    status: str | None = None
    baseline: str | dict | list | None = None
    expected: str | dict | list | None = None
    day7: str | dict | list | None = None
    day30: str | dict | list | None = None
    targetMet: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    requirementId: str | None = None
    projectId: str | None = None

class ValueRequestRow(ResponseDTO):
    id: str
    demandId: str | None = None
    stage: str | None = None
    token: str | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    status: str | None = None
    scheduledAt: str | None = None
    notificationStatus: str | None = None
    notificationError: str | None = None
    sentAt: str | None = None
    submittedAt: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    requirementId: str | None = None
    projectId: str | None = None
    responseSnapshot: str | dict | list | None = None
    viewedAt: str | None = None

class PostlaunchRow(ResponseDTO):
    id: str
    requirementId: str | None = None
    projectId: str | None = None
    demandId: str | None = None
    deliveryKind: str | None = None
    deliveryDate: str | None = None
    useStartDate: str | None = None
    businessOwnerUserId: str | None = None
    businessOwnerName: str | None = None
    status: str | None = None
    day7DueDate: str | None = None
    day30DueDate: str | None = None
    day7RequestId: str | None = None
    day30RequestId: str | None = None
    notes: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    deliveryRoundId: str | None = None
    acceptanceRequestId: str | None = None
    acceptanceSnapshot: str | None = None
    verificationExemption: str | None = None
    plannedDeliveryDate: str | None = None

class IssueRow(ResponseDTO):
    id: str
    operationId: str | None = None
    requirementId: str | None = None
    projectId: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None
    dueDate: str | None = None
    resolution: str | None = None
    rootCause: str | None = None
    prevention: str | None = None
    discoveredAt: str | None = None
    firstResponseAt: str | None = None
    resolvedAt: str | None = None
    reopenedCount: int | bool | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    closedAt: str | None = None

class ProposalRow(ResponseDTO):
    id: str
    operationId: str | None = None
    requirementId: str | None = None
    projectId: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    title: str | None = None
    problem: str | None = None
    suggestion: str | None = None
    expectedChange: str | None = None
    status: str | None = None
    linkedRequirementId: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    adoptedAt: str | None = None

class KnowledgeRow(ResponseDTO):
    id: str
    operationId: str | None = None
    requirementId: str | None = None
    projectId: str | None = None
    title: str | None = None
    content: str | dict | list | None = None
    artifactType: str | None = None
    sourceType: str | None = None
    sourceId: str | None = None
    status: str | None = None
    ownerUserId: str | None = None
    ownerName: str | None = None
    createdByUserId: str | None = None
    createdByName: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    publishedAt: str | None = None

class CollectionBatchRow(ResponseDTO):
    id: str
    notificationId: str | None = None
    targetType: str | None = None
    targetValue: str | None = None
    targetLabel: str | None = None
    message: str | None = None
    status: str | None = None
    recipientCount: int | bool | None = None
    successCount: int | bool | None = None
    failureCount: int | bool | None = None
    responseCount: int | bool | None = None
    pendingCount: int | bool | None = None
    valuableCount: int | bool | None = None
    excludedCount: int | bool | None = None
    sentByUserId: str | None = None
    sentByName: str | None = None
    sentAt: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    requestKey: str | None = None
    runKey: str | None = None
    acceptedCount: int | bool | None = None
    unknownCount: int | bool | None = None

class CollectionResponseRow(ResponseDTO):
    id: str
    batchId: str | None = None
    notificationId: str | None = None
    recipientToken: str | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    recipientDepartment: str | None = None
    topicKey: str | None = None
    topicLabel: str | None = None
    title: str | None = None
    problem: str | None = None
    frequency: str | None = None
    desired: str | None = None
    description: str | None = None
    department: str | None = None
    expectedDeliveryTime: str | None = None
    businessPriority: str | None = None
    intakeLevel: str | None = None
    responseData: str | dict | list | None = None
    judgment: str | None = None
    judgmentReason: str | None = None
    similarDemandId: str | None = None
    nextAction: str | None = None
    judgedByUserId: str | None = None
    judgedByName: str | None = None
    judgedAt: str | None = None
    convertedDemandId: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None

class CollectionNotificationRow(ResponseDTO):
    id: str
    targetType: str | None = None
    targetValue: str | None = None
    targetLabel: str | None = None
    recipientUserIds: str | list | None = None
    recipientNames: str | list | None = None
    message: str | None = None
    link: str | None = None
    sentByUserId: str | None = None
    sentByName: str | None = None
    status: str | None = None
    successCount: int | bool | None = None
    failureCount: int | bool | None = None
    error: str | None = None
    sentAt: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    entryMode: str | None = None
    demandId: str | None = None
    scheduleCycle: str | None = None
    scheduleTime: str | None = None
    scheduleDay: int | None = None
    enabled: int | bool | None = None
    lastSentDate: str | None = None
    scheduleWeekdays: str | list | None = None
    requestKey: str | None = None

