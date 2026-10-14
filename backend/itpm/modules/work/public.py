"""Public work API consumed by project/work workflows.

Commands: create/update/soft-delete, log and phase facts in shared UoW.
Queries: requirement, phases, templates, progress, iterations/releases.
Other modules cannot access WorkRepository; cross-domain policies and side
effects are explicit workflow calls. No HTTP, commit or provider here.
"""
from typing import Protocol
from .rules import classification,transition,TERMINAL
class WorkPort(Protocol):
    def requirement(self,uow,identifier:str,lock:bool=False)->dict|None: ...
    def progress(self,uow,project_id:str)->dict: ...
    def initial(self,uow,principal,project:dict,phase_keys:list|None=None)->dict: ...
