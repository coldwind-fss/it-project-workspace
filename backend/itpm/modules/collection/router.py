from .schemas import CollectionNotification, CollectionSchedule, CollectionResponse, CollectionJudgment
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from itpm.core.errors import require

def router(http, collection, sender):
    r = ContractRouter()
    c = collection

    def batch(u, p, bid):
        c.identity.action(u, p, 'demand_pool.manage')
        row = c.batch(u, bid)
        require(row, '主动征集批次不存在', 404, 'NOT_FOUND')
        return c.batch_payload(u, row, True)

    def response(u, p, rid):
        c.identity.action(u, p, 'demand_pool.manage')
        row = c.response(u, rid)
        require(row, '主动征集回执不存在', 404, 'NOT_FOUND')
        return c.response_payload(u, row)

    @r.get('/api/demand-pool/notifications')
    def notices(request: Request):

        def execute(u, p):
            c.identity.action(u, p, 'demand_pool.manage')
            return c.notices(u)
        return http.call(request, execute)

    @r.post('/api/demand-pool/notifications')
    def send(data: CollectionNotification, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: sender.send(u, p, data))

    @r.put('/api/demand-pool/notifications/{notification_id}')
    def update(notification_id: str, data: CollectionSchedule, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: c.update_notice(u, p, notification_id, data))

    @r.get('/api/demand-collections/batches')
    def batches(request: Request):

        def execute(u, p):
            c.identity.action(u, p, 'demand_pool.manage')
            return c.batches(u)
        return http.call(request, execute)

    @r.get('/api/demand-collections/batches/{batch_id}')
    def detail(batch_id: str, request: Request):
        return http.call(request, lambda u, p: batch(u, p, batch_id))

    @r.post('/api/demand-collections/batches/{batch_id}/retry-failures')
    def retry(batch_id: str, request: Request):
        return http.call(request, lambda u, p: sender.retry(u, p, batch_id))

    @r.post('/api/demand-collections/responses')
    def submit(data: CollectionResponse, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: c.submit_response(u, data))

    @r.get('/api/demand-collections/responses/{response_id}')
    def response_detail(response_id: str, request: Request):
        return http.call(request, lambda u, p: response(u, p, response_id))

    @r.put('/api/demand-collections/responses/{response_id}')
    def judge(response_id: str, data: CollectionJudgment, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: c.judge(u, p, response_id, data))
    return r
