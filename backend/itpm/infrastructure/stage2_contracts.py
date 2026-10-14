from itpm.core.stage2_responses import *
from pydantic import Field


class AttachmentView(AttachmentRow):
    isImage:bool
    isVideo:bool
    url:str
class MessageView(MessageRow):
    messageTypeLabel:str
    attachments:list[AttachmentView]
class CommentView(SharedCommentRow):
    attachments:list[AttachmentView]
class ActivityView(SharedActivityRow):
    activityTypeLabel:str
    attachments:list[AttachmentView]
    comments:list[CommentView]
    commentCount:int
class CollaborationView(CollaborationRow):
    kindLabel:str
    statusLabel:str
    attachments:list[AttachmentView]
    canHandle:bool
    requirementLink:str
    messages:list[MessageView]|None=None
    messageCount:int|None=None
class IntakeView(IntakeRow):
    kindLabel:str
    statusLabel:str
    attachments:list[AttachmentView]
    canHandle:bool
    requirementLink:str
    businessUrgencyLabel:str
class ReviewView(ReviewRow):
    reviewerRoleLabel:str
    statusLabel:str
    decisionLabel:str
    branchDecisions:dict|list
    link:str
    canSubmit:bool
    canManage:bool
    demand:dict|None=None
class ConfirmationView(ConfirmationRow):
    content:dict
    templateType:str
    templateLabel:str
    statusLabel:str
    link:str
    canConfirm:bool
    canManage:bool|None=None
    demand:dict|None=None
class ValueRequestView(ValueRequestRow):
    stageLabel:str
    statusLabel:str
    responseSnapshot:dict
    link:str
class ValueCardView(ValueCardRow):
    baseline:dict
    expected:dict
    day7:dict
    day30:dict
    policy:dict|None=None
class DemandView(DemandRow):
    intakeLevelLabel:str
    statusLabel:str
    evaluationDecisionLabel:str
    businessPriorityLabel:str
    solutionTypeLabel:str
    aiModeLabel:str
    pocRequirementLabel:str
    impactScopeLabel:str
    complexityLevelLabel:str
    attachments:list[AttachmentView]
    requirementLink:str
    requirementIds:list[str]
    requirements:list[dict]
    l3Branches:list[BranchRow]
    hasL3Decomposition:bool
    confirmation:ConfirmationView|None=None
    reviews:list[ReviewView]
    reviewSummary:dict[str,int]
    evaluations:list[dict]
    supplements:list[SupplementRow]
    pocs:list[PoolPocRow]
    valueCard:ValueCardView|None=None
    outcomeRequests:list[ValueRequestView]
    valuePolicy:dict
    canEvaluate:bool
    canEdit:bool
    canDelete:bool
class ConversionView(ResponseDTO):
    demand:DemandView
    requirementId:str
    requirementIds:list[str]
    requirementTitle:str|None=None
class LifecycleView(ResponseDTO):
    canEdit:bool
    sources:list[dict]
    baselines:list[BaselineRow]
    links:list[dict]
    operations:list[dict]
    attachments:list[AttachmentView]
class BaselinesView(ResponseDTO):
    canEdit:bool
    templateType:str
    templateLabel:str
    items:list[BaselineRow]
class LinkView(ResponseDTO):
    id:str
    kind:str
    kindLabel:str
    status:str
    expiresAt:str
    snapshot:dict
    outcome:str
    outcomeLabel:str
    submittedAt:str
    response:dict|None=None
    draftAttachments:list[AttachmentView]
class PostlaunchView(PostlaunchRow):
    title:str
    issueCount:int
    openIssueCount:int
    knowledgeCount:int
    proposalCount:int
    projectType:str
    actualDeliveryDate:str
    valueVerificationEligibility:dict
    valueVerificationEligible:bool
    acceptanceOutcome:str
    outcomeRequests:list[ValueRequestView]
    day7Request:ValueRequestView|None=None
    day30Request:ValueRequestView|None=None
    valueVerificationStatus:str
    lifecycleStage:str
    lifecycleProgress:int
    dataStatus:str
    metricDataStatus:dict
    businessPriority:str
    businessPriorityLabel:str
    issues:list[IssueRow]|None=None
    proposals:list[ProposalRow]|None=None
    knowledge:list[KnowledgeRow]|None=None
class CollectionResponseView(CollectionResponseRow):
    judgmentLabel:str
    responseData:dict
    attachments:list[AttachmentView]
    convertedDemand:dict|None=None
class CollectionBatchView(CollectionBatchRow):
    deliveryPendingCount:int
    deliveryStatusCounts:dict[str,int]
    deliveries:list[dict]
    responses:list[CollectionResponseView]
class Option(ResponseDTO):
    key:str
    label:str
class DemandOptions(ResponseDTO):
    statuses:list[Option]
    decisions:list[Option]
    priorities:list[Option]
    intakeLevels:list[Option]
    solutionTypes:list[Option]
    aiModes:list[Option]
    pocRequirements:list[Option]
    impactScopes:list[Option]
    complexityLevels:list[Option]
    valueLevels:list[Option]
    nextActions:list[Option]
    templates:dict[str,list[dict]]
    reviewRoles:list[Option]
    reviewDecisions:list[Option]
class IntakeOptions(ResponseDTO):
    kinds:list[Option]
    statuses:list[Option]
    urgencies:list[Option]
    collaborationKinds:list[Option]
    collaborationStatuses:list[Option]
class DecompositionView(ResponseDTO):
    demand:DemandView
    branches:list[BranchRow]
class DemandResult(ResponseDTO):
    demand:DemandView
class ReviewAssignmentView(DemandResult):
    reviews:list[ReviewView]
    createdCount:int|None=None
    reused:bool|None=None
class EntryContext(ResponseDTO):
    valid:bool
    notificationId:str
    entryMode:str
    demandId:str
    recipientUserId:str
    recipientName:str
    department:str
    usedAt:str
    demand:dict|None=None
class OutcomeContext(ResponseDTO):
    request:ValueRequestView
    demand:dict
    stage:dict[str,str]
    valueCard:ValueCardView|dict
class OutcomeResult(ResponseDTO):
    request:ValueRequestView
    status:str
    stage:str
class CollectionNotificationView(CollectionNotificationRow):
    recipientUserIds:list[str]
    recipientNames:list[str]
    unknownCount:int|None=None
    batchId:str|None=None
    failureDetails:list[dict]|None=None
class RetryCollectionView(ResponseDTO):
    status:str
    successCount:int
    failureCount:int
    failureDetails:list[dict]
    batch:CollectionBatchView
class ApiOk(ResponseDTO):
    ok:int|bool

CONTRACTS={
 ('GET','/api/todos'):list[TodoRow],('PUT','/api/todos/{tid}/read'):TodoRow,('PUT','/api/todos/{tid}/done'):TodoRow,
 ('POST','/api/business-attachments'):AttachmentView,('DELETE','/api/business-attachments/{attachment_id}'):ApiOk,
 ('GET','/api/collaboration-link/context'):LinkView,('POST','/api/collaboration-link/submit'):LinkView,('POST','/api/collaboration-link/attachments'):AttachmentView,
 ('GET','/api/business-requests/options'):IntakeOptions,('GET','/api/demand-pool/options'):DemandOptions,
 ('PUT','/api/demand-pool/{demand_id}/decomposition'):DecompositionView,('PUT','/api/demand-pool/{demand_id}/branch-decisions'):DemandResult,
 ('POST','/api/demand-pool/{demand_id}/reviews'):ReviewAssignmentView,('POST','/api/demand-pool/{demand_id}/reviews/reuse'):ReviewAssignmentView,
 ('GET','/api/demand-pool/entry-context'):EntryContext,('POST','/api/demand-pool/materials'):SupplementRow,
 ('GET','/api/demand-pool/{demand_id}/supplements'):list[SupplementRow],('POST','/api/demand-pool/{demand_id}/supplements'):SupplementRow,
 ('GET','/api/demand-pool-supplements/{supplement_id}'):SupplementRow,('PUT','/api/demand-pool-supplements/{supplement_id}'):SupplementRow,
 ('GET','/api/demand-pool/{demand_id}/pocs'):list[PoolPocRow],('POST','/api/demand-pool/{demand_id}/pocs'):PoolPocRow,('PUT','/api/demand-pool-pocs/{poc_id}'):PoolPocRow,
 ('GET','/api/demand-pool/notifications'):list[CollectionNotificationView],('POST','/api/demand-pool/notifications'):CollectionNotificationView,
 ('PUT','/api/demand-pool/notifications/{notification_id}'):CollectionNotificationView,
 ('POST','/api/demand-collections/batches/{batch_id}/retry-failures'):RetryCollectionView,
 ('GET','/api/demand-pool-outcome-context'):OutcomeContext,('POST','/api/demand-pool-outcome-submit'):OutcomeResult|ValueRequestView,
 ('DELETE','/api/demand-pool/{demand_id}'):ApiOk,('POST','/api/collaboration-links/{link_id}/revoke'):ApiOk,
 ('GET','/api/business-requests'):list[IntakeView],('POST','/api/business-requests'):IntakeView,('PUT','/api/business-requests/{business_id}'):IntakeView,
 ('GET','/api/business-collaborations'):list[CollaborationView],('POST','/api/business-collaborations'):CollaborationView,
 ('PUT','/api/business-collaborations/{collaboration_id}'):CollaborationView,
 ('GET','/api/requirements/{requirement_id}/business-collaborations'):list[CollaborationView],('POST','/api/requirements/{requirement_id}/business-collaborations'):CollaborationView,
 ('GET','/api/business-collaborations/{collaboration_id}/messages'):list[MessageView],('POST','/api/business-collaborations/{collaboration_id}/messages'):CollaborationView,
 ('GET','/api/requirements/{requirement_id}/shared-activities'):list[ActivityView],('POST','/api/requirements/{requirement_id}/shared-activities'):ActivityView,
 ('GET','/api/projects/{project_id}/shared-activities'):list[ActivityView],('POST','/api/projects/{project_id}/shared-activities'):ActivityView,
 ('GET','/api/shared-activities/{activity_id}/comments'):list[CommentView],('POST','/api/shared-activities/{activity_id}/comments'):CommentView,
 ('GET','/api/demand-pool'):list[DemandView],('POST','/api/demand-pool'):DemandView|CollectionResponseView,
 ('GET','/api/demand-pool/{demand_id}'):DemandView,('PUT','/api/demand-pool/{demand_id}'):DemandView,
 ('POST','/api/demand-pool/{demand_id}/convert'):ConversionView,('POST','/api/demand-pool/{demand_id}/historical-decomposition'):ConversionView,
 ('POST','/api/demand-pool/{demand_id}/confirmations'):ConfirmationView,('POST','/api/demand-pool/{demand_id}/confirmations/resend'):ConfirmationView,
 ('GET','/api/demand-pool-confirmations/by-token'):ConfirmationView,('POST','/api/demand-pool-confirmations/by-token'):ConfirmationView,
 ('GET','/api/demand-pool-confirmations/{confirmation_id}'):ConfirmationView,('POST','/api/demand-pool-confirmations/{confirmation_id}'):ConfirmationView,
 ('GET','/api/demand-pool-reviews/by-token'):ReviewView,('POST','/api/demand-pool-reviews/by-token'):ReviewView,
 ('GET','/api/demand-pool-reviews/{review_id}'):ReviewView,('POST','/api/demand-pool-reviews/{review_id}'):ReviewView,
 ('GET','/api/requirements/{rid}/lifecycle'):LifecycleView,('GET','/api/requirements/{rid}/delivery-baselines'):BaselinesView,
 ('POST','/api/requirements/{rid}/delivery-baselines'):BaselineRow,('POST','/api/requirements/{rid}/collaboration-links'):LinkView,
 ('POST','/api/requirements/{rid}/deliveries'):PostlaunchView,('POST','/api/delivery-feedback/{feedback_id}/route'):FeedbackRow,
 ('GET','/api/demand-pool/{demand_id}/value-card'):ValueCardView,('PUT','/api/demand-pool/{demand_id}/value-card'):ValueCardView,
 ('GET','/api/postlaunch/operations'):list[PostlaunchView],('POST','/api/postlaunch/operations'):PostlaunchView,
 ('GET','/api/postlaunch/operations/{operation_id}'):PostlaunchView,('PUT','/api/postlaunch/operations/{operation_id}'):PostlaunchView,
 ('POST','/api/postlaunch/issues'):IssueRow,('PUT','/api/postlaunch/issues/{issue_id}'):IssueRow,
 ('POST','/api/postlaunch/proposals'):ProposalRow,('POST','/api/postlaunch/knowledge'):KnowledgeRow,
 ('GET','/api/demand-collections/batches'):list[CollectionBatchView],('GET','/api/demand-collections/batches/{batch_id}'):CollectionBatchView,
 ('POST','/api/demand-collections/responses'):CollectionResponseView,('GET','/api/demand-collections/responses/{response_id}'):CollectionResponseView,
 ('PUT','/api/demand-collections/responses/{response_id}'):CollectionResponseView,
}
for root,key in [('demand-pool','demand_id'),('requirements','requirement_id'),('projects','project_id')]:
    CONTRACTS['GET','/api/'+root+'/{'+key+'}/outcome-requests']=list[ValueRequestView]
    CONTRACTS['POST','/api/'+root+'/{'+key+'}/outcome-requests']=ValueRequestView
for action in ['send','view']:CONTRACTS['POST','/api/demand-pool-value-requests/{request_id}/'+action]=ValueRequestView
