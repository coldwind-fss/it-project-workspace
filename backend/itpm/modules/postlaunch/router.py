from .schemas import PostlaunchWrite, PostlaunchIssueWrite, PostlaunchProposalWrite, PostlaunchKnowledgeWrite
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from .dashboard_schemas import PostlaunchDashboard

def router(http, postlaunch):
    r = ContractRouter()
    s = postlaunch

    @r.get('/api/postlaunch/operations')
    def operations(request: Request, status: str='', department: str='', keyword: str=''):
        return http.call(request, lambda u, p: s.list(u, p, status, department, keyword), read=True)

    @r.post('/api/postlaunch/operations')
    def create(data: PostlaunchWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.register(u, p, data))

    @r.get('/api/postlaunch/operations/{operation_id}')
    def detail(operation_id: str, request: Request):
        return http.call(request, lambda u, p: s.detail(u, p, operation_id), read=True)

    @r.put('/api/postlaunch/operations/{operation_id}')
    def update(operation_id: str, data: PostlaunchWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.update_operation(u, p, operation_id, data))

    @r.get('/api/postlaunch/dashboard',response_model=PostlaunchDashboard,response_model_exclude_unset=True)
    def dashboard(request: Request, department: str='', keyword: str='', period: str='all', deliveryMonth: str='', solutionType: str='', lifecycleStage: str='', valueStatus: str='', businessPriority: str=''):
        filters = {'department': department, 'keyword': keyword, 'period': period, 'deliveryMonth': deliveryMonth, 'solutionType': solutionType, 'lifecycleStage': lifecycleStage, 'valueStatus': valueStatus, 'businessPriority': businessPriority}
        return http.call(request, lambda u, p: s.dashboard(u, p, filters), read=True)

    @r.post('/api/postlaunch/issues')
    def issue(data: PostlaunchIssueWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.create_issue(u, p, data))

    @r.put('/api/postlaunch/issues/{issue_id}')
    def update_issue(issue_id: str, data: PostlaunchIssueWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.update_issue(u, p, issue_id, data))

    @r.post('/api/postlaunch/proposals')
    def proposal(data: PostlaunchProposalWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.create_artifact(u, p, data))

    @r.post('/api/postlaunch/knowledge')
    def knowledge(data: PostlaunchKnowledgeWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.create_artifact(u, p, data, True))
    return r
