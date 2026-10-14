from pydantic import BaseModel, ConfigDict


class SharedWrite(BaseModel):
    model_config = ConfigDict(extra='allow')
    activityType: str = 'work_progress'
    title: str = ''
    content: str = ''


class CommentWrite(BaseModel):
    model_config = ConfigDict(extra='allow')
    content: str = ''


class ThreadWrite(BaseModel):
    model_config = ConfigDict(extra='allow')
    requirementId: str = ''
    kind: str = 'clarification'
    title: str = ''
    content: str = ''
    recipientName: str = ''
    recipientUserId: str = ''
    dueDate: str = ''


class ThreadReply(BaseModel):
    model_config = ConfigDict(extra='allow')
    content: str = ''
    messageType: str = 'message'
    status: str = ''


class IntakeWrite(BaseModel):
    model_config = ConfigDict(extra='allow')
    kind: str = 'new_requirement'
    title: str = ''
    originalFeedback: str = ''
    projectId: str = ''
    requirementId: str = ''
