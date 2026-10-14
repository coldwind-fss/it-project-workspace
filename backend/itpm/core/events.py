from dataclasses import dataclass, field, asdict,replace
from copy import deepcopy
from typing import Callable
import hashlib,json

EVENT_TYPES = frozenset({'project_created', 'project_updated', 'requirement_created',
    'requirement_updated', 'requirement_assigned', 'requirement_delivered', 'todo_created',
    'shared_activity_created', 'shared_activity_comment_created'})

def legacy_dedupe_key(event_type,record):
    identity=record.get('activityId') or record.get('commentId') or record.get('id') or record.get('requirementId') or record.get('projectId') or 'unknown'
    version=record.get('updatedAt') or record.get('createdAt') or record.get('submittedAt') or ''
    fingerprint=hashlib.sha1(json.dumps(record,ensure_ascii=False,sort_keys=True,default=str).encode('utf-8')).hexdigest()[:12]
    return f'event:{event_type}:{identity}:{version}:{fingerprint}'


@dataclass(frozen=True)
class Event:
    event_type: str
    event_id: str
    source_ref: str
    occurred_at: str
    actor: dict
    aggregate_type: str
    aggregate_id: str
    payload: dict
    correlation_id: str = ''
    causation_id: str = ''
    dedupe_key: str = ''
    schema_version: int = 1

    def __post_init__(self):
        if self.event_type not in EVENT_TYPES:
            raise ValueError('unknown event type')
        object.__setattr__(self, 'payload', deepcopy(self.payload))

@dataclass(frozen=True)
class DeferredEvent:
    snapshot: Event
    complete: Callable
    def resolve(self):
        payload=self.complete(deepcopy(self.snapshot.payload))
        key=legacy_dedupe_key(self.snapshot.event_type,payload)
        return replace(self.snapshot,payload=payload,dedupe_key=key,event_id='evt'+hashlib.sha256(key.encode()).hexdigest()[:24])

@dataclass(frozen=True)
class AfterCommitAction:
    run: Callable


class Dispatcher:
    """Synchronous, after commit. No durable outbox or replay claim."""
    def __init__(self):
        self.events: list[Event] = []
        self.subscribers: list[Callable] = []
        self.failures: list[dict] = []

    def dispatch(self, events):
        for event in events:
            if isinstance(event,AfterCommitAction):
                try:event.run()
                except Exception:self.failures.append({'code':'INTEGRATION_UNAVAILABLE'})
                continue
            if isinstance(event,DeferredEvent):
                try:event=event.resolve()
                except Exception:
                    self.failures.append({'eventId':event.snapshot.event_id,'code':'INTEGRATION_UNAVAILABLE'})
                    continue
            self.events.append(event)
            for subscriber in self.subscribers:
                try:
                    subscriber(event)
                except Exception:
                    self.failures.append({'eventId': event.event_id, 'code': 'INTEGRATION_UNAVAILABLE'})
