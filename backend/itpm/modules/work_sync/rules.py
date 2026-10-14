"""Pure work-sync mappings and preview DTO construction."""

import re,json,hashlib

from datetime import datetime

from itpm.core.errors import AppError

def operator_display_name(p): return p.get("devOwnerName") or p.get("name") or "系统"

REQUIREMENT_IMPACT_OPTIONS = ['核心', '重要', '常规']

REQUIREMENT_WORKLOAD_OPTIONS = ['大', '中', '小']

REQUIREMENT_STATUS_OPTIONS = ['待处理', '进行中', '待交付', '已交付', '已关闭']

REQUIREMENT_STATUS_MAP = {'待评估': '待处理', '已立项': '待处理', '已排期': '待处理', '需求确认中': '进行中', '设计中': '进行中', '开发中': '进行中', '联调中': '进行中', '测试中': '进行中', '迭代中': '进行中', '维护中': '进行中', '暂停中': '进行中', 'active': '进行中', 'paused': '进行中', '待上线': '待交付', '已上线': '已交付', '已关闭': '已关闭', '已归档': '已关闭', 'archived': '已关闭'}

REQUIREMENT_TYPE_MAP = {'新功能': '新增功能', '能力新增': '新增功能', '优化改进': '功能优化', '能力优化': '功能优化', 'Bug修复': '问题修复', 'UI调整': '功能优化', '接口对接': '技术建设', '技术重构': '功能优化', '需求变更': '业务确认', '需求对接': '业务确认', '技术方案验证': '技术建设', '功能测试': '验证交付'}

REQUIREMENT_TYPE_OPTIONS = ['业务确认', '需求重构', '产品设计', '技术建设', '新增功能', '功能优化', '问题修复', '验证交付']

REQUIREMENT_CHANGE_OBJECT_OPTIONS = ['模块', '功能', '字段', '流程', '页面交互', '接口数据', '系统基础', '其他']

L3_ITEM_KIND_LABELS = {'initial_build': '初始建设', 'feature': '新功能 / 模块', 'bugfix': '问题修复', 'enhancement': '功能优化', 'integration': '接口 / 数据集成', 'design': '产品设计', 'operation': '运营维护'}

WORK_SYNC_SERVICE_TOKEN_ENV = 'PM_WORK_SYNC_TOKEN'

WORK_SYNC_SERVICE_HEADER = 'X-PM-Work-Sync-Token'

WORK_SYNC_SERVICE_USER_ID = 'work-sync-service'

WORK_SYNC_SERVICE_NAME = '开发工作同步服务'

WORK_SYNC_SERVICE_TOKEN_MIN_LENGTH = 32

WORK_SYNC_KIND_TYPE_MAP = {'feature': '新增功能', 'new_feature': '新增功能', 'module': '新增功能', 'refactor': '技术建设', 'bug': '问题修复', 'bug_fix': '问题修复', 'ui': '功能优化', 'design': '产品设计', 'business': '业务确认', 'integration': '技术建设', 'validation': '验证交付', 'operations': '技术建设', 'optimization': '功能优化'}

WORK_SYNC_PHASE_STATUS_MAP = {'planned': '待处理', 'todo': '待处理', 'in_progress': '进行中', 'doing': '进行中', 'delivered': '已交付', 'done': '已交付', 'closed': '已关闭'}

WORK_SYNC_IMPACT_MAP = {'core': '核心', 'critical': '核心', 'high': '核心', 'important': '重要', 'medium': '重要', 'normal': '常规', 'ordinary': '常规', 'low': '常规'}

WORK_SYNC_EFFORT_MAP = {'large': '大', 'big': '大', 'high': '大', 'medium': '中', 'moderate': '中', 'normal': '中', 'small': '小', 'low': '小'}

WORK_SYNC_CHANGE_OBJECT_MAP = {'feature': '功能', 'new_feature': '模块', 'module': '模块', 'refactor': '系统基础', 'bug': '功能', 'bug_fix': '功能', 'ui': '页面交互', 'design': '流程', 'business': '流程', 'integration': '接口数据', 'validation': '功能', 'operations': '系统基础', 'optimization': '功能'}

WORK_SYNC_LOG_TYPE_MAP = {'progress': '工作进展', 'work': '工作进展', 'problem': '遇到问题', 'issue': '遇到问题', 'delivery': '交付说明', 'delivered': '交付说明', 'next_step': '下一步', 'next': '下一步'}

def _work_sync_normalize_name(value):
    return re.sub('\\s+', '', str(value or '')).strip().lower()

def _work_sync_datetime(value, fallback=None, *, generated_at):
    fallback = fallback or generated_at
    text = str(value or '').strip().replace('T', ' ')
    if not text:
        return fallback
    if re.fullmatch('\\d{4}-\\d{2}-\\d{2}', text):
        return text + ' 00:00:00'
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M'):
        try:
            return datetime.strptime(text, fmt).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    return fallback

def _work_sync_date(value, fallback=None, *, generated_at):
    return _work_sync_datetime(value, fallback or generated_at, generated_at=generated_at)[:10]

def _work_sync_map_log_type(value):
    text = str(value or '').strip()
    return WORK_SYNC_LOG_TYPE_MAP.get(text.lower(), text if text in {'工作进展', '遇到问题', '交付说明', '下一步'} else '工作进展')

def _work_sync_normalize_item(item, index, project, source, operator, *, generated_at):
    if not isinstance(item, dict):
        raise AppError(f'records[{index}] 必须是对象', 400)
    title = str(item.get('title') or '').strip()
    if not title:
        raise AppError(f'records[{index}].title 必填', 400)
    if len(title) > 300:
        raise AppError(f'records[{index}].title 最多300字', 400)
    kind_raw = str(item.get('kind') or item.get('workKind') or 'feature').strip()
    kind = kind_raw.lower().replace('-', '_').replace(' ', '_')
    item_kind = str(item.get('itemKind') or '').strip().lower().replace('-', '_').replace(' ', '_')
    item_kind = item_kind or {'new_feature': 'feature', 'module': 'feature', 'feature': 'feature', 'refactor': 'enhancement', 'bug': 'bugfix', 'bug_fix': 'bugfix', 'ui': 'enhancement', 'design': 'design', 'business': 'feature', 'integration': 'integration', 'validation': 'feature', 'operations': 'operation', 'optimization': 'enhancement'}.get(kind, 'feature')
    if item_kind not in L3_ITEM_KIND_LABELS:
        item_kind = 'feature'
    requested_type = str(item.get('type') or '').strip()
    work_type = requested_type or WORK_SYNC_KIND_TYPE_MAP.get(kind, '功能优化')
    phase = str(item.get('phase') or '').strip().lower().replace('-', '_')
    requested_status = str(item.get('status') or '').strip()
    status = requested_status or WORK_SYNC_PHASE_STATUS_MAP.get(phase, '待处理')
    priority = str(item.get('priority') or 'P2').strip()
    impact_raw = str(item.get('impactLevel') or item.get('impact') or '常规').strip()
    impact = WORK_SYNC_IMPACT_MAP.get(impact_raw.lower(), impact_raw)
    effort_raw = str(item.get('workloadLevel') or item.get('effort') or '中').strip()
    effort = WORK_SYNC_EFFORT_MAP.get(effort_raw.lower(), effort_raw)
    change_object = str(item.get('changeObject') or WORK_SYNC_CHANGE_OBJECT_MAP.get(kind, '功能')).strip()
    work_date = _work_sync_date(item.get('workDate') or item.get('occurredAt') or source.get('rangeEnd') or source.get('endDate'), generated_at=generated_at)
    expected = str(item.get('expectedDeliveryTime') or work_date).strip()
    operator_name = operator_display_name(operator)
    assignee = str(item.get('developerOwner') or item.get('assignee') or operator.get('devOwnerName') or '').strip()
    requester = str(item.get('businessOwner') or item.get('requester') or '').strip()
    if operator.get('isService'):
        if not assignee or not requester:
            raise AppError(f'records[{index}] 必须明确 developerOwner（开发负责人）和 businessOwner（业务负责人）', 400)
        if assignee == WORK_SYNC_SERVICE_NAME or requester == WORK_SYNC_SERVICE_NAME:
            raise AppError(f'records[{index}] 的负责人不能填写接口服务身份，请填写真实开发负责人和业务负责人', 400)
    else:
        assignee = assignee or operator_name or '待分配'
        requester = requester or operator_name
    description = str(item.get('summary') or item.get('description') or '').strip()
    acceptance = str(item.get('acceptance') or item.get('acceptanceCriteria') or '').strip()
    if not acceptance:
        acceptance = f'完成“{title}”并形成可验证的交付结果'
    labels = item.get('labels', '')
    if isinstance(labels, list):
        labels = ','.join((str(x).strip() for x in labels if str(x).strip()))
    logs = item.get('logs') if isinstance(item.get('logs'), list) else item.get('workLogs')
    if not isinstance(logs, list):
        logs = []
    if len(logs) > 100:
        raise AppError(f'records[{index}].logs 最多100条', 400)
    normalized_logs = []
    for log_index, log in enumerate(logs):
        if not isinstance(log, dict):
            raise AppError(f'records[{index}].logs[{log_index}] 必须是对象', 400)
        content = str(log.get('content') or '').strip()
        if not content:
            continue
        if len(content) > 5000:
            raise AppError(f'records[{index}].logs[{log_index}].content 最多5000字', 400)
        normalized_logs.append({'logType': _work_sync_map_log_type(log.get('type') or log.get('logType')), 'content': content, 'occurredAt': _work_sync_datetime(log.get('occurredAt') or work_date + ' 00:00:00', work_date + ' 00:00:00', generated_at=generated_at)})
    has_explicit_logs = bool(normalized_logs)
    if work_type not in REQUIREMENT_TYPE_OPTIONS:
        work_type = REQUIREMENT_TYPE_MAP.get(work_type, '功能优化')
    if status not in REQUIREMENT_STATUS_OPTIONS:
        status = REQUIREMENT_STATUS_MAP.get(status, '待处理')
    if priority not in {'P0', 'P1', 'P2', 'P3', 'P4'}:
        priority = 'P2'
    if impact not in REQUIREMENT_IMPACT_OPTIONS:
        impact = '常规'
    if effort not in REQUIREMENT_WORKLOAD_OPTIONS:
        effort = '中'
    if change_object not in REQUIREMENT_CHANGE_OBJECT_OPTIONS:
        change_object = '功能'
    if not normalized_logs:
        fallback_content = description or f'已同步开发工作记录，当前状态：{status}'
        normalized_logs = [{'logType': '交付说明' if status in ('已交付', '已关闭') else '工作进展', 'content': fallback_content, 'occurredAt': work_date + ' 00:00:00'}]
    try:
        story_points = int(item.get('storyPoints') or 0)
    except (TypeError, ValueError):
        story_points = 0
    if story_points <= 0:
        story_points = {'大': 3, '中': 2, '小': 1}.get(effort, 2)
    return {'title': title, 'kind': kind, 'itemKind': item_kind, 'parentRequirementId': str(item.get('parentRequirementId') or '').strip()[:80], 'versionTarget': str(item.get('versionTarget') or project.get('currentVersion') or '').strip()[:120], 'phaseTemplateKeys': item.get('phaseTemplateKeys') if isinstance(item.get('phaseTemplateKeys'), list) else [], 'type': work_type, 'status': status, 'priority': priority, 'impactLevel': impact, 'workloadLevel': effort, 'changeObject': change_object, 'workDate': work_date, 'expectedDeliveryTime': expected, 'assignee': assignee, 'requester': requester, 'department': str(item.get('department') or project.get('department') or '').strip(), 'description': description, 'acceptanceCriteria': acceptance, 'storyPoints': story_points, 'labels': str(labels or ''), 'logs': normalized_logs, 'hasExplicitLogs': has_explicit_logs, 'writeMode': str(item.get('writeMode') or item.get('action') or '').strip().lower(), 'sourceRefs': item.get('sourceRefs') if isinstance(item.get('sourceRefs'), list) else []}

def _work_sync_source(data):
    source = data.get('source') if isinstance(data.get('source'), dict) else {}
    return {'type': str(source.get('type') or data.get('sourceType') or 'development-session').strip(), 'ref': str(source.get('ref') or source.get('threadId') or data.get('sourceRef') or '').strip(), 'rangeStart': str(source.get('rangeStart') or source.get('startDate') or data.get('sourceRangeStart') or '').strip(), 'rangeEnd': str(source.get('rangeEnd') or source.get('endDate') or data.get('sourceRangeEnd') or '').strip()}

def _work_sync_payload_hash(data, project):
    body = {k: v for k, v in data.items() if k not in {'mode', 'idempotencyKey'}}
    body['resolvedProjectId'] = project.get('id')
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def _work_sync_preview_item(index, item, project, existing):
    requested = item.get('writeMode')
    if requested == 'skip':
        action, reason = ('skip', '调用方指定跳过')
    elif requested == 'create' and existing:
        action, reason = ('needs_review', '目标项目下已有同名记录，不能强制重复创建')
    elif requested == 'append' and (not existing):
        action, reason = ('needs_review', '没有找到可追加的同名记录')
    elif existing:
        action = 'append' if item.get('hasExplicitLogs') else 'skip'
        reason = '发现同名记录，将追加工作动态' if action == 'append' else '发现同名记录且没有新动态'
    else:
        action, reason = ('create', '未发现同名记录')
    return {'index': index, 'action': action, 'reason': reason, 'title': item.get('title'), 'existingRequirementId': existing.get('id') if existing else '', 'mapped': {'kind': item.get('kind'), 'itemKind': item.get('itemKind'), 'type': item.get('type'), 'status': item.get('status'), 'priority': item.get('priority'), 'impactLevel': item.get('impactLevel'), 'workloadLevel': item.get('workloadLevel'), 'workDate': item.get('workDate'), 'logCount': len(item.get('logs') or [])}}

def _work_sync_result(project, batch_id, idempotency_key, source, items, status='preview'):
    summary = {key: 0 for key in ('total', 'create', 'append', 'skip', 'needsReview')}
    summary['total'] = len(items)
    for item in items:
        key = {'needs_review': 'needsReview'}.get(item.get('action'), item.get('action'))
        if key in summary:
            summary[key] += 1
    return {'status': status, 'batchId': batch_id or '', 'idempotencyKey': idempotency_key, 'source': source, 'project': {'id': project.get('id'), 'name': project.get('name'), 'department': project.get('department') or ''}, 'summary': summary, 'items': items}
