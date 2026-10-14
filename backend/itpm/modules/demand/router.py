from .schemas import DemandCreate, DemandEvaluation, DemandDecomposition, DemandConversion, BranchDecisions, ReviewAssignment, ReviewReuse, ReviewSubmission, ConfirmationCreate, ConfirmationSubmission, SupplementCreate, SupplementSubmission, MaterialsSubmission, PoolPocCreate, PoolPocUpdate
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from itpm.core.errors import require

def router(http, demand, workflow, notices, collection):
    r = ContractRouter()
    v = demand.v

    def current(u, p, did):
        row = demand.get(u, did, active=True)
        require(row and demand.visible(u, p, row), '需求池记录不存在或无权访问', 404, 'NOT_FOUND')
        return row

    @r.get('/api/demand-pool/options')
    def options(request: Request):
        keys = {'statuses': 'STATUS_OPTIONS', 'decisions': 'DECISION_OPTIONS', 'priorities': 'PRIORITY_OPTIONS', 'intakeLevels': 'INTAKE_LEVEL_OPTIONS', 'solutionTypes': 'SOLUTION_TYPES', 'aiModes': 'AI_OPTIONS', 'pocRequirements': 'POC_OPTIONS', 'impactScopes': 'IMPACT_SCOPE_OPTIONS', 'complexityLevels': 'COMPLEXITY_OPTIONS', 'nextActions': 'NEXT_ACTION_OPTIONS', 'templates': 'TEMPLATE_QUESTIONS', 'reviewDecisions': 'REVIEW_DECISION_OPTIONS'}
        return http.call(request, lambda u, p: {**{k: v['DEMAND_POOL_' + x] for k, x in keys.items()}, 'valueLevels': [{'key': k, 'label': x} for k, x in v['DEMAND_POOL_VALUE_LEVEL_LABELS'].items()], 'reviewRoles': [{'key': k, 'label': x} for k, x in v['DEMAND_POOL_REVIEW_ROLE_LABELS'].items()]}, read=True)

    @r.get('/api/demand-pool')
    def demands(request: Request, status: str='', department: str=''):
        return http.call(request, lambda u, p: demand.list(u, p, status, department), read=True)

    @r.post('/api/demand-pool')
    def create(data: DemandCreate, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            token = collection.token(u, str(data.get('recipientToken') or '').strip())
            if token:
                require(token.get('entryMode') != 'materials', '该链接用于补充已有需求，请使用资料补充表单')
                if token.get('entryMode') == 'collect':
                    return collection.submit_response(u, data | {'problem': data.get('problem') or data.get('description') or data.get('content') or ''})
                p = collection.actor(token)
            else:
                demand.identity.action(u, p, 'business_request.submit')
            row = demand.create(u, p, data, token)
            if token:
                collection.used(u, token, row['id'])
            return demand.payload(u, p, row)
        return http.call(request, execute)

    @r.get('/api/demand-pool/entry-context')
    def entry(request: Request, token: str=''):
        return http.call(request, lambda u, p: collection.entry(u, token))

    @r.post('/api/demand-pool/materials')
    def materials(data: MaterialsSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            token = collection.token(u, str(data.get('recipientToken') or data.get('token') or '').strip())
            if token and token.get('entryMode') == 'materials':
                p = collection.actor(token)
            else:
                demand.identity.action(u, p, 'business_request.submit')
                token = None
            did = str(data.get('demandId') or (token or {}).get('demandId') or '').strip()
            result = demand.materials(u, p, did, data)
            if token:
                collection.used(u, token, did)
            return result
        return http.call(request, execute)

    @r.get('/api/demand-pool/{demand_id}')
    def detail(demand_id: str, request: Request):
        return http.call(request, lambda u, p: demand.payload(u, p, current(u, p, demand_id)), read=True)

    @r.put('/api/demand-pool/{demand_id}')
    def update(demand_id: str, data: DemandEvaluation, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: demand.payload(u, p, demand.update(u, p, demand_id, data)))

    @r.delete('/api/demand-pool/{demand_id}')
    def delete(demand_id: str, request: Request):
        return http.call(request, lambda u, p: demand.delete(u, p, demand_id))

    @r.put('/api/demand-pool/{demand_id}/decomposition')
    def decompose(demand_id: str, data: DemandDecomposition, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            branches = demand.save_branches(u, p, demand_id, data)
            return {'demand': demand.payload(u, p, demand.get(u, demand_id)), 'branches': branches}
        return http.call(request, execute)

    @r.put('/api/demand-pool/{demand_id}/branch-decisions')
    def decisions(demand_id: str, data: BranchDecisions, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            demand.branch_decisions(u, p, demand_id, data)
            return {'demand': demand.payload(u, p, demand.get(u, demand_id))}
        return http.call(request, execute)

    @r.post('/api/demand-pool/{demand_id}/convert')
    def convert(demand_id: str, data: DemandConversion, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: workflow.convert(u, p, demand_id, data))

    @r.post('/api/demand-pool/{demand_id}/historical-decomposition')
    def historical(demand_id: str, data: DemandDecomposition, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: workflow.historical(u, p, demand_id, data))

    @r.post('/api/demand-pool/{demand_id}/reviews')
    def reviews(demand_id: str, data: ReviewAssignment, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            created, resend, row = demand.assign_reviews(u, p, demand_id, data)

            def refresh(read):
                return {'demand': demand.payload(read, p, demand.get(read, demand_id)), 'reviews': [demand.review_payload(read, p, x) for x in demand.rows(read, 'demand_pool_reviews', demand_id)], 'createdCount': len(created)}
            result = refresh(u)
            notices.send_after_commit(u, p, 'demand_pool_reviews', created + resend, row, result, refresh)
            return result
        return http.call(request, execute)

    @r.post('/api/demand-pool/{demand_id}/reviews/reuse')
    def reuse(demand_id: str, data: ReviewReuse, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            demand.reuse_review(u, p, demand_id, data)
            return {'demand': demand.payload(u, p, demand.get(u, demand_id)), 'reviews': [demand.review_payload(u, p, x) for x in demand.rows(u, 'demand_pool_reviews', demand_id)], 'reused': True}
        return http.call(request, execute)

    def review_action(u, p, identifier, token, data=None):
        row, d, p = demand.review_form(u, p, identifier, token)
        if data is not None:
            demand.submit_review(u, p, row, d, data)
            row, d = demand.joined_form(u, 'demand_pool_reviews', row['id'])
        result = demand.review_payload(u, p, row, bool(token))
        result['demand'] = demand.review_demand(u, d, token)
        return result

    @r.get('/api/demand-pool-reviews/by-token')
    def review_token(request: Request, token: str=''):
        return http.call(request, lambda u, p: review_action(u, p, '', token))

    @r.post('/api/demand-pool-reviews/by-token')
    def submit_review_token(data: ReviewSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: review_action(u, p, '', str(data.get('token') or '').strip(), data))

    @r.get('/api/demand-pool-reviews/{review_id}')
    def review_id(review_id: str, request: Request, token: str=''):
        return http.call(request, lambda u, p: review_action(u, p, review_id, token))

    @r.post('/api/demand-pool-reviews/{review_id}')
    def submit_review_id(review_id: str, data: ReviewSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: review_action(u, p, review_id, str(data.get('token') or '').strip(), data))

    @r.post('/api/demand-pool/{demand_id}/confirmations')
    def confirmation(demand_id: str, data: ConfirmationCreate, request: Request):
        data = data.model_dump(exclude_unset=True)

        def execute(u, p):
            row, d = demand.create_confirmation(u, p, demand_id, data)
            return {**demand.confirmation_payload(u, p, row), 'demandId': demand_id, 'demandTitle': d['title']}
        return http.call(request, execute)

    @r.post('/api/demand-pool/{demand_id}/confirmations/resend')
    def resend(demand_id: str, request: Request):

        def execute(u, p):
            demand.identity.action(u, p, 'demand_pool.manage')
            d = demand.get(u, demand_id)
            require(d, '需求池记录不存在', 404, 'NOT_FOUND')
            row = demand.latest_confirmation(u, demand_id, 'pending')
            require(row, '尚未生成上线前交付与价值确认链接')

            def refresh(read):
                return {**demand.confirmation_payload(read, p, demand.source(read, 'demand_pool_confirmations', row['id'])), 'demandId': demand_id, 'demandTitle': d['title']}
            result = refresh(u)
            notices.send_after_commit(u, p, 'demand_pool_confirmations', [row], d, result, refresh)
            return result
        return http.call(request, execute)

    def confirmation_action(u, p, identifier, token, data=None):
        row, d, p = demand.confirmation_form(u, p, identifier, token)
        if data is not None:
            demand.submit_confirmation(u, p, row, d, data)
            row, d = demand.joined_form(u, 'demand_pool_confirmations', row['id'])
        result = demand.confirmation_payload(u, p, row, bool(token) and data is None)
        result['demand'] = {k: d.get(k) for k in ['id', 'title', 'description', 'department', 'requesterUserId', 'requesterName', 'status', 'projectName', 'solutionType']}
        return result

    @r.get('/api/demand-pool-confirmations/by-token')
    def confirmation_token(request: Request, token: str=''):
        return http.call(request, lambda u, p: confirmation_action(u, p, '', token))

    @r.post('/api/demand-pool-confirmations/by-token')
    def submit_confirmation_token(data: ConfirmationSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: confirmation_action(u, p, '', str(data.get('token') or '').strip(), data))

    @r.get('/api/demand-pool-confirmations/{confirmation_id}')
    def confirmation_id(confirmation_id: str, request: Request):
        return http.call(request, lambda u, p: confirmation_action(u, p, confirmation_id, ''))

    @r.post('/api/demand-pool-confirmations/{confirmation_id}')
    def submit_confirmation_id(confirmation_id: str, data: ConfirmationSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: confirmation_action(u, p, confirmation_id, '', data))

    @r.get('/api/demand-pool/{demand_id}/supplements')
    def supplements(demand_id: str, request: Request):

        def execute(u, p):
            current(u, p, demand_id)
            return [demand.supplement_payload(u, x, False, False) for x in reversed(demand.rows(u, 'demand_pool_supplements', demand_id))]
        return http.call(request, execute, read=True)

    @r.post('/api/demand-pool/{demand_id}/supplements')
    def supplement_create(demand_id: str, data: SupplementCreate, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: demand.create_supplement(u, p, demand_id, data))

    @r.get('/api/demand-pool-supplements/{supplement_id}')
    def supplement(supplement_id: str, request: Request):
        return http.call(request, lambda u, p: demand.supplement(u, p, supplement_id), read=True)

    @r.put('/api/demand-pool-supplements/{supplement_id}')
    def supplement_submit(supplement_id: str, data: SupplementSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: demand.supplement(u, p, supplement_id, data))

    @r.get('/api/demand-pool/{demand_id}/pocs')
    def pocs(demand_id: str, request: Request):

        def execute(u, p):
            current(u, p, demand_id)
            return [{**x, 'attachments': demand.files.list(u, 'demand_pool_poc', x['id'])} for x in reversed(demand.rows(u, 'demand_pool_pocs', demand_id))]
        return http.call(request, execute, read=True)

    @r.post('/api/demand-pool/{demand_id}/pocs')
    def poc_create(demand_id: str, data: PoolPocCreate, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: demand.create_poc(u, p, demand_id, data))

    @r.put('/api/demand-pool-pocs/{poc_id}')
    def poc_update(poc_id: str, data: PoolPocUpdate, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: demand.update_poc(u, p, poc_id, data))
    return r
