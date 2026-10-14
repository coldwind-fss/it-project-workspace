from .schemas import ValueCardWrite, OutcomeRequestWrite, OutcomeSubmission
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from itpm.core.errors import require

def router(http, value, workflow, demand):
    r = ContractRouter()

    @r.get('/api/demand-pool-outcome-context')
    def context(request: Request, token: str=''):
        return http.call(request, lambda u, p: workflow.context(u, token))

    @r.post('/api/demand-pool-outcome-submit')
    def submit(data: OutcomeSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: workflow.submit(u, data))

    @r.get('/api/demand-pool/{demand_id}/value-card')
    def card(demand_id: str, request: Request):

        def execute(u, p):
            d = demand.get(u, demand_id)
            require(demand.visible(u, p, d), '需求池记录不存在或无权访问', 404, 'NOT_FOUND')
            row = value.card(u, {'demandId': demand_id})
            return {**(row or {'id': '', 'demandId': demand_id, 'status': 'draft', 'baseline': {}, 'expected': {}, 'day7': {}, 'day30': {}, 'targetMet': '', 'ownerName': ''}), 'policy': value.policy(d)}
        return http.call(request, execute, read=True)

    @r.put('/api/demand-pool/{demand_id}/value-card')
    def save_card(demand_id: str, data: ValueCardWrite, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            demand.identity.action(u, p, 'demand_pool.manage')
            d = demand.get(u, demand_id)
            require(d, '需求池记录不存在', 404, 'NOT_FOUND')
            row = value.save_card(u, p, d, data)
            demand.audit.record(u, p, 'DEMAND_POOL', demand_id, d['title'], 'value_card_update', '更新成果验证记录', after={'status': row['status'], 'targetMet': row['targetMet']})
            return {**row, 'policy': value.policy(d)}
        return http.call(request, execute)

    @r.get('/api/demand-pool/{demand_id}/outcome-requests')
    def demands(demand_id: str, request: Request):
        return http.call(request, lambda u, p: workflow.list(u, p, 'demand', demand_id), read=True)

    @r.post('/api/demand-pool/{demand_id}/outcome-requests')
    def demand_create(demand_id: str, data: OutcomeRequestWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: workflow.create(u, p, 'demand', demand_id, data))

    @r.get('/api/requirements/{requirement_id}/outcome-requests')
    def requirements(requirement_id: str, request: Request):
        return http.call(request, lambda u, p: workflow.list(u, p, 'requirement', requirement_id), read=True)

    @r.post('/api/requirements/{requirement_id}/outcome-requests')
    def requirement_create(requirement_id: str, data: OutcomeRequestWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: workflow.create(u, p, 'requirement', requirement_id, data))

    @r.get('/api/projects/{project_id}/outcome-requests')
    def projects(project_id: str, request: Request):
        return http.call(request, lambda u, p: workflow.list(u, p, 'project', project_id), read=True)

    @r.post('/api/projects/{project_id}/outcome-requests')
    def project_create(project_id: str, data: OutcomeRequestWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: workflow.create(u, p, 'project', project_id, data))

    @r.post('/api/demand-pool-value-requests/{request_id}/send')
    def send(request_id: str, request: Request):
        return http.call(request, lambda u, p: workflow.send(u, p, request_id))

    @r.post('/api/demand-pool-value-requests/{request_id}/view')
    def view(request_id: str, request: Request):
        return http.call(request, lambda u, p: workflow.view(u, p, request_id))
    return r
