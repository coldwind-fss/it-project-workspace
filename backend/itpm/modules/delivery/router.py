from .schemas import DeliveryBaselineWrite, CollaborationLinkWrite, DeliveryWrite, DeliveryFeedbackRoute, CollaborationSubmission
from fastapi import Request, File, Form, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from itpm.infrastructure.router import ContractRouter
from itpm.core.errors import AppError

def router(http, workflow):
    r = ContractRouter()
    s = workflow

    def token(request):
        return request.headers.get('X-PM-Collaboration-Token', '')

    @r.get('/api/requirements/{rid}/lifecycle')
    def detail(rid: str, request: Request):
        return http.call(request, lambda u, p: s.detail(u, p, rid))

    @r.get('/api/requirements/{rid}/delivery-baselines')
    def baselines(rid: str, request: Request):
        return http.call(request, lambda u, p: s.list_baselines(u, p, rid))

    @r.post('/api/requirements/{rid}/delivery-baselines')
    def baseline(rid: str, data: DeliveryBaselineWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.create_baseline(u, p, rid, data))

    @r.post('/api/requirements/{rid}/collaboration-links')
    def link(rid: str, data: CollaborationLinkWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.create_link(u, p, rid, data))

    @r.post('/api/requirements/{rid}/deliveries')
    def deliver(rid: str, data: DeliveryWrite, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.deliver(u, p, rid, data))

    @r.post('/api/delivery-feedback/{feedback_id}/route')
    def feedback(feedback_id: str, data: DeliveryFeedbackRoute, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.route_feedback(u, p, feedback_id, data))

    @r.post('/api/collaboration-links/{link_id}/revoke')
    def revoke(link_id: str, request: Request):
        return http.call(request, lambda u, p: s.revoke(u, p, link_id))

    @r.get('/api/collaboration-link/context')
    def context(request: Request):
        result = http.call(request, lambda u, p: s.public_payload(u, s.token_link(u, token(request))))
        return JSONResponse(result, headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})

    @r.post('/api/collaboration-link/submit')
    def submit(data: CollaborationSubmission, request: Request):
        data = data.model_dump(exclude_unset=True)
        return http.call(request, lambda u, p: s.submit(u, token(request), data))

    @r.get('/api/collaboration-link/attachments/{attachment_id}')
    def download(attachment_id: str, request: Request):

        def execute(u, p):
            row, path = s.download(u, token(request), attachment_id)
            return FileResponse(path, filename=row['originalName'], headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})
        return http.call(request, execute)

    @r.post('/api/collaboration-link/attachments')
    async def upload(request: Request, file: UploadFile=File(...), uploadKey: str=Form(...)):
        content = bytearray()
        try:
            while (chunk := (await file.read(1024 * 1024))):
                content.extend(chunk)
                if len(content) > 50 * 1024 * 1024:
                    raise AppError('单个附件不能超过 50MB', 413, 'TOO_LARGE', field='detail')
            return http.call(request, lambda u, p: s.upload(u, token(request), uploadKey, file.filename, file.content_type, content))
        finally:
            await file.close()
    return r
