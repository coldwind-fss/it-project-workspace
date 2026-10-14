"""Identity public API: resolve/action/resource checks, contacts and policies.

Consumers: HTTP dependency and project/work workflows. Commands accept explicit
UoW, not Request. Queries never write. AUTH_REQUIRED=401; FORBIDDEN=403.
"""
from typing import Protocol
from itpm.core.ports import Principal
from .rules import same_name,split_people

class IdentityPort(Protocol):
    def resolve(self, uow, token: str) -> Principal: ...
    def action(self, uow, principal: Principal, action: str) -> None: ...
    def can_edit(self, uow, principal: Principal, resource: dict, entity: str, project: dict | None = None) -> bool: ...
    def person_id(self, uow, name: str) -> str: ...
