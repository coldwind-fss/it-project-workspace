from pydantic import BaseModel, ConfigDict

class Command(BaseModel):
    model_config=ConfigDict(extra="allow")

class ValueCardWrite(Command):
    baseline: dict | str | None = None
    baselineSummary: str | None = None
    expected: dict | str | None = None
    expectedSummary: str | None = None
    day7: dict | str | None = None
    day7Summary: str | None = None
    day30: dict | str | None = None
    day30Summary: str | None = None
    ownerName: str | None = None
    ownerUserId: str | None = None
    status: str | None = None
    targetMet: str | list | bool | None = None

class OutcomeRequestWrite(Command):
    stage: str | None = None
    recipientUserId: str | None = None
    recipientName: str | None = None
    scheduledAt: str | None = None
    sendNow: bool | None = None

class OutcomeSubmission(Command):
    token: str | None = None
    currentState: str | None = None
    desiredChange: str | None = None
    summary: str | None = None
    actualResult: str | None = None
    noGoal: bool | None = None
    useStatus: str | None = None
    goalStatus: str | None = None
    satisfaction: str | None = None
    issueLevel: str | None = None
    effectStatus: str | None = None
    changeTypes: str | list | bool | None = None
    targetMet: str | list | bool | None = None
    metricResults: list | None = None

