from pydantic import BaseModel, ConfigDict

class Command(BaseModel):
    model_config=ConfigDict(extra="allow")

class CollectionNotification(Command):
    requestKey: str | None = None
    entryMode: str | None = None
    mode: str | None = None
    demandId: str | None = None
    scheduleCycle: str | None = None
    scheduleTime: str | None = None
    scheduleDay: int | str | None = None
    scheduleWeekdays: list | None = None
    targetType: str | None = None
    targetValue: str | None = None
    department: str | None = None
    recipientName: str | None = None
    targetUserId: str | None = None
    recipientUserId: str | None = None
    message: str | None = None
    sendNow: bool | None = None

class CollectionSchedule(Command):
    enabled: bool | None = None

class CollectionResponse(Command):
    recipientToken: str | None = None
    problem: str | None = None
    department: str | None = None
    topicKey: str | None = None
    topicLabel: str | None = None
    frequency: str | None = None
    desired: str | None = None
    description: str | None = None
    expectedDeliveryTime: str | None = None
    businessPriority: str | None = None

class CollectionJudgment(Command):
    judgment: str | None = None
    judgmentReason: str | None = None
    reason: str | None = None
    similarDemandId: str | None = None
    nextAction: str | None = None

