"""Shared HTTP contract registration, preserving original response shapes."""
from fastapi import APIRouter
from itpm.core.responses import (CategoryRow,ProjectRow,RequirementRow,PhaseRow,WorkLogRow,SprintRow,ReleaseRow,ChangelogRow,OperationRow,AppLogRow,Ok,NamedId,Identifier,BulkResult,ProjectCreated,DingConfig,LoginResult)
from pydantic import BaseModel,ConfigDict

class PersonnelResult(BaseModel):
    model_config=ConfigDict(extra='allow')
    accessRoles:list[dict]
    assignments:list[dict]
    customRoles:list[dict]
    permissionGroups:list[dict]
    todoSettings:dict
    users:list[dict]
    operator:dict

class ContactsResult(BaseModel):
    model_config=ConfigDict(extra='allow')
    users:list[dict]
    developers:list[dict]
    businessOwners:list[str]
    departments:list
    admins:list[dict]

CONTRACTS={
 ('GET','/api/categories'):list[CategoryRow],('GET','/api/categories/{cid}'):CategoryRow,('GET','/api/categories/{cid}/projects'):list[ProjectRow],
 ('POST','/api/categories'):NamedId,('PUT','/api/categories/{cid}'):CategoryRow,('DELETE','/api/categories/{cid}'):Ok,
 ('GET','/api/projects'):list[ProjectRow],('GET','/api/projects/{pid}'):ProjectRow,('POST','/api/projects'):ProjectCreated,('PUT','/api/projects/{pid}'):ProjectRow,
 ('DELETE','/api/projects/{pid}'):Ok,('POST','/api/projects/bulk-delete'):BulkResult,
 ('GET','/api/requirements'):list[RequirementRow],('GET','/api/requirements/live'):list[RequirementRow],('GET','/api/requirements/{rid}'):RequirementRow,
 ('POST','/api/requirements'):NamedId,('PUT','/api/requirements/{rid}'):RequirementRow,('DELETE','/api/requirements/{rid}'):Ok,
 ('POST','/api/requirements/bulk-delete'):BulkResult,('POST','/api/requirements/bulk-classification'):BulkResult,
 ('GET','/api/requirements/{rid}/work-logs'):list[WorkLogRow],('POST','/api/requirements/{rid}/work-logs'):WorkLogRow,
 ('GET','/api/requirements/{rid}/phases'):list[PhaseRow],('POST','/api/requirements/{rid}/phases'):PhaseRow,('PUT','/api/requirements/{rid}/phases/{phase_id}'):PhaseRow,
 ('GET','/api/changelogs'):list[ChangelogRow],('GET','/api/requirements/{rid}/changelogs'):list[ChangelogRow],
 ('GET','/api/sprints'):list[SprintRow],('GET','/api/sprints/{sid}'):SprintRow,('POST','/api/sprints'):NamedId,('PUT','/api/sprints/{sid}'):SprintRow,('DELETE','/api/sprints/{sid}'):Ok,
 ('GET','/api/releases'):list[ReleaseRow],('GET','/api/releases/{rid}'):ReleaseRow,('POST','/api/releases'):Identifier,
 ('GET','/api/operations'):list[OperationRow],('GET','/api/app-logs'):list[AppLogRow],('POST','/api/app-logs'):Ok,
 ('GET','/api/dingtalk/config'):DingConfig,('POST','/api/dingtalk/login'):LoginResult,('GET','/api/dingtalk/options'):ContactsResult,
 ('GET','/api/system/personnel'):PersonnelResult,('PUT','/api/system/personnel'):Ok,
}

class ContractRouter(APIRouter):
    def add_api_route(self,path,endpoint,**kwargs):
        method=next(iter(kwargs.get('methods',[]) or []),None)
        from .stage2_contracts import CONTRACTS as stage2_contracts
        if (method,path) in stage2_contracts:
            kwargs.update(response_model=stage2_contracts[method,path],response_model_exclude_unset=True)
        if (method,path) in CONTRACTS:
            kwargs.update(response_model=CONTRACTS[method,path],response_model_exclude_unset=True)
        return super().add_api_route(path,endpoint,**kwargs)
