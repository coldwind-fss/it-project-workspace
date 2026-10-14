from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Protocol
import uuid


class Clock(Protocol):
    def now(self) -> str: ...

class NotificationGateway(Protocol):
    def config(self) -> dict: ...
    def exchange(self,code:str) -> dict: ...
    def contacts(self) -> dict: ...
    def refresh_contacts(self) -> None: ...
    def union_id(self,userid:str) -> str: ...
    def send_markdown_to_users(self,recipients:list[str],title:str,markdown:str) -> dict: ...
    def send_group_markdown(self,webhook:str,secret:str,title:str,markdown:str) -> dict: ...
    def complete_todo(self,recipient_union:str,task_id:str,operator_union:str) -> dict: ...
    def close(self) -> None: ...


class SystemClock:
    def now(self):
        return datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')


class Ids:
    def new(self, prefix: str, length=10):
        return prefix + uuid.uuid4().hex[:length]


@dataclass(frozen=True)
class Principal:
    userId: str = ''
    name: str = '匿名用户'
    role: str = 'viewer'
    devOwnerName: str = ''
    isDeveloper: bool = False
    authenticated: bool = False

    def dto(self):
        from dataclasses import asdict
        return asdict(self)
