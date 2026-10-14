from pydantic import BaseModel, ConfigDict

class Command(BaseModel):
    model_config=ConfigDict(extra="allow")

class DeliveryBaselineWrite(Command):
    content: dict | None = None
    templateType: str | None = None
    recipientName: str | None = None
    recipientUserId: str | None = None
    send: bool | None = None
    validDays: int | str | None = None
    attachmentIds: list | None = None

class CollaborationLinkWrite(Command):
    clientKey: str | None = None
    kind: str | None = None
    title: str | None = None
    content: str | None = None
    recipientName: str | None = None
    baselineId: str | None = None
    attachmentIds: list | None = None
    validDays: int | str | None = None
    collaborationId: str | None = None

class DeliveryWrite(Command):
    clientKey: str | None = None
    acceptanceRequestId: str | None = None
    verificationExemption: str | None = None
    deliveryDate: str | None = None
    useStartDate: str | None = None
    deliveryKind: str | None = None
    notes: str | None = None
    businessOwnerName: str | None = None
    businessOwnerUserId: str | None = None
    plannedDeliveryDate: str | None = None

class DeliveryFeedbackRoute(Command):
    routeType: str | None = None

class CollaborationSubmission(Command):
    outcome: str | None = None
    content: str | None = None
    feedbackType: str | None = None
    requestedTitle: str | None = None

