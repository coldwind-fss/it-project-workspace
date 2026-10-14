"""Portfolio public commands/query. Shared UoW supplied by workflows.

get_project -> active raw project or None; list -> joins categories read-only.
create/update/category -> local table facts. Cross-domain initial work,
progress/phase templates, audit and external events belong to workflows.
"""
from typing import Protocol
from .rules import solution_type,validate_project
class PortfolioPort(Protocol):
    def project(self,uow,identifier:str,lock:bool=False)->dict|None: ...
    def create_project(self,uow,principal,data:dict)->dict: ...
