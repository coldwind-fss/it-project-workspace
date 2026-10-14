import hashlib
import hmac
import json
import time
from fastapi import Request
from itpm.infrastructure.router import ContractRouter
from itpm.core.errors import require
from itpm.core.ports import Principal
from .schemas import SharedWrite, CommentWrite, ThreadWrite, ThreadReply, IntakeWrite


def router(http, workflow, service, vocabulary):
    r = ContractRouter()
    dump = lambda model: model.model_dump(exclude_unset=True)

    @r.get('/api/business-requests/options')
    def intake_options(request: Request):
        return http.call(request, lambda u, p: {'kinds': vocabulary['BUSINESS_INTAKE_KIND_OPTIONS'],
            'statuses': vocabulary['BUSINESS_INTAKE_STATUS_OPTIONS'], 'urgencies': vocabulary['BUSINESS_URGENCY_OPTIONS'],
            'collaborationKinds': vocabulary['BUSINESS_COLLABORATION_KIND_OPTIONS'],
            'collaborationStatuses': vocabulary['BUSINESS_COLLABORATION_STATUS_OPTIONS']}, read=True)

    @r.get('/api/business-requests')
    def intake_list(request: Request, status: str = ''):
        return http.call(request, lambda u, p: service.list_threads(u, p, status, intake=True), read=True)

    @r.post('/api/business-requests')
    def intake_create(data: IntakeWrite, request: Request):
        return http.call(request, lambda u, p: workflow.intake(u, p, dump(data)))

    @r.post('/api/business-requests/webhook')
    async def webhook(request: Request):
        secret = http.settings.intake_webhook_secret
        require(secret, '业务协作 webhook 尚未配置', 503, 'NOT_CONFIGURED')
        timestamp = request.headers.get('X-PM-Intake-Timestamp') or ''
        try:
            timestamp_value = int(timestamp)
        except ValueError:
            require(False, '缺少有效的 webhook 时间戳', 401, 'INVALID_SIGNATURE')
        require(abs(int(time.time()) - timestamp_value) <= 300, 'webhook 请求已过期', 401, 'EXPIRED')
        raw = await request.body()
        expected = hmac.new(secret.encode(), (timestamp + '.').encode() + raw, hashlib.sha256).hexdigest()
        provided = request.headers.get('X-PM-Intake-Signature', '').removeprefix('sha256=')
        require(provided and hmac.compare_digest(provided, expected), 'webhook 签名无效', 401, 'INVALID_SIGNATURE')
        try:
            data = json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            require(False, 'webhook body 必须是 JSON')
        require(isinstance(data, dict), 'webhook body 必须是对象')
        actor = Principal(userId=str(data.get('requesterUserId') or '').strip(), name=str(data.get('requesterName') or '').strip(), authenticated=True)
        data['sourceType'] = data.get('sourceType') or 'dingtalk_webhook'
        data['sourceRef'] = data.get('sourceRef') or request.headers.get('X-PM-Source-Ref') or ''
        return http.call(request, lambda u, p: workflow.intake(u, actor, data, True))

    @r.put('/api/business-requests/{business_id}')
    def intake_update(business_id: str, data: dict, request: Request):
        return http.call(request, lambda u, p: workflow.update_intake(u, p, business_id, data))

    @r.get('/api/business-collaborations/options')
    def thread_options(request: Request):
        return http.call(request, lambda u, p: {'kinds': vocabulary['BUSINESS_COLLABORATION_KIND_OPTIONS'],
            'statuses': vocabulary['BUSINESS_COLLABORATION_STATUS_OPTIONS']}, read=True)

    @r.get('/api/business-collaborations')
    def threads(request: Request, status: str = ''):
        return http.call(request, lambda u, p: service.list_threads(u, p, status), read=True)

    @r.post('/api/business-collaborations')
    def create_thread(data: ThreadWrite, request: Request):
        return http.call(request, lambda u, p: workflow.create_thread(u, p, data.requirementId, dump(data)))

    @r.get('/api/requirements/{requirement_id}/business-collaborations')
    def work_threads(requirement_id: str, request: Request):
        return http.call(request, lambda u, p: service.list_threads(u, p, rid=requirement_id), read=True)

    @r.post('/api/requirements/{requirement_id}/business-collaborations')
    def create_work_thread(requirement_id: str, data: ThreadWrite, request: Request):
        return http.call(request, lambda u, p: workflow.create_thread(u, p, requirement_id, dump(data)))

    @r.put('/api/business-collaborations/{collaboration_id}')
    def update_thread(collaboration_id: str, data: dict, request: Request):
        return http.call(request, lambda u, p: workflow.update_thread(u, p, collaboration_id, data))

    @r.get('/api/business-collaborations/{collaboration_id}/messages')
    def messages(collaboration_id: str, request: Request):
        def execute(u, p):
            row = service.get_thread(u, p, collaboration_id)
            return [service.message_payload(u, m) for m in service.projected_messages(u, row)]
        return http.call(request, execute, read=True)

    @r.post('/api/business-collaborations/{collaboration_id}/messages')
    def message(collaboration_id: str, data: ThreadReply, request: Request):
        return http.call(request, lambda u, p: workflow.update_thread(u, p, collaboration_id, dump(data), True))

    @r.get('/api/requirements/{requirement_id}/shared-activities')
    def activities(requirement_id: str, request: Request):
        return http.call(request, lambda u, p: service.activities(u, p, 'requirement', requirement_id), read=True)

    @r.get('/api/projects/{project_id}/shared-activities')
    def project_activities(project_id: str, request: Request):
        return http.call(request, lambda u, p: service.activities(u, p, 'project', project_id), read=True)

    @r.post('/api/requirements/{requirement_id}/shared-activities')
    def create_activity(requirement_id: str, data: SharedWrite, request: Request):
        return http.call(request, lambda u, p: workflow.shared(u, p, 'requirement', requirement_id, dump(data)))

    @r.post('/api/projects/{project_id}/shared-activities')
    def create_project_activity(project_id: str, data: SharedWrite, request: Request):
        return http.call(request, lambda u, p: workflow.shared(u, p, 'project', project_id, dump(data)))

    @r.get('/api/shared-activities/{activity_id}/comments')
    def comments(activity_id: str, request: Request):
        def execute(u, p):
            row = service.activity(u, activity_id)
            require(row, '共享动态不存在', 404, 'NOT_FOUND')
            require(service.activity_visible(u, p, row), '当前身份不是该动态的参与者', 403, 'FORBIDDEN')
            return [service.comment_payload(u, m) for m in service.projected_comments(u, row)]
        return http.call(request, execute, read=True)

    @r.post('/api/shared-activities/{activity_id}/comments')
    def comment(activity_id: str, data: CommentWrite, request: Request):
        return http.call(request, lambda u, p: workflow.comment(u, p, activity_id, data.content))
    return r
