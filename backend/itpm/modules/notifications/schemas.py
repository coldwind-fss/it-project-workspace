from pydantic import BaseModel,ConfigDict

class NotificationWrite(BaseModel):
    model_config=ConfigDict(extra='allow')
    name:str|None=None
    webhook:str|None=None
    secret:str|None=None
    deliveryChannel:str|None=None
    cardTargetType:str|None=None
    cardConversationId:str|None=None
    cardTemplateId:str|None=None
    cardRobotCode:str|None=None
    recipientName:str|None=None
    recipientUserId:str|None=None
    scope:str|None=None
    targetType:str|None=None
    projectId:str|None=None
    requirementId:str|None=None
    developer:str|None=None
    developerUserId:str|None=None
    ownerUserId:str|None=None
    ownerName:str|None=None
    contentTypes:list[str]|str|None=None
    customContent:str|None=None
    enabled:bool|int|None=None
    scheduleTime:str|None=None
    scheduleCycle:str|None=None
    scheduleDay:int|str|None=None
    scheduleWeekdays:list[int|str]|str|None=None
    triggerType:str|None=None
    triggerEvents:list[str]|str|None=None
    reportScene:str|None=None
    contentRange:str|None=None
    customRangeStart:str|None=None
    customRangeEnd:str|None=None
class NotificationView(NotificationWrite):
    id:str|None=None
    contentTypes:list[str]
    triggerEvents:list[str]
    scheduleWeekdays:list[int]
    enabled:bool
    canManage:bool|None=None
    webhookMasked:str
    createdAt:str|None=None
    updatedAt:str|None=None
    lastSentDate:str|None=None
    lastSentAt:str
    lastSendStatus:str
    lastSendError:str
class DeliveryLog(BaseModel):
    id:str
    targetId:str
    targetName:str
    triggerType:str
    eventType:str
    dedupeKey:str
    status:str
    error:str
    sentAt:str
    createdAt:str
    updatedAt:str
class NotificationSync(BaseModel):
    targetId:str|None=None
    scope:str|None=None
    developer:str|None=None
    developerUserId:str|None=None
class NotificationResult(BaseModel):
    model_config=ConfigDict(extra='allow')
    ok:int
    title:str|None=None
    markdown:str|None=None
    result:dict|None=None
    sent:int|None=None
    skipped:bool|None=None
