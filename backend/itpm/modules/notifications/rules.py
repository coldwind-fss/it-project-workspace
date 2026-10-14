"""Notification rule values and Markdown rendering over explicit facts/time."""

import json

from datetime import datetime,timedelta

from itpm.modules.identity.public import same_name as same_person_name

from itpm.modules.insights.public import LEGACY_STATUS_MAP,STATUS_SHORT_LABELS,l3_profile_text

def canonical_developer_name(name): return name or ""

def parse_list_field(val, fallback=None):
    if not val:
        return fallback or []
    if isinstance(val, list):
        return val
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, list) else fallback or []
    except Exception:
        return fallback or []

NOTIFICATION_EVENT_OPTIONS = {'project_created': '新增项目', 'project_updated': '项目资料更新', 'requirement_created': '新增需求', 'requirement_updated': '需求内容更新', 'requirement_assigned': '需求负责人变更', 'requirement_delivered': '需求交付/上线', 'todo_created': '生成待办', 'shared_activity_created': '发布共享动态', 'shared_activity_comment_created': '评论共享动态'}

NOTIFICATION_REPORT_SCENES = {'daily': '每日工作同步', 'weekly': '每周工作与产品动态', 'milestone': '重要产品事件'}

REPORTING_ACTIVE_STATUSES = {'待处理', '进行中', '待交付', '受阻'}

def notification_weekday_values(schedule_cycle='daily', raw_value=None, fallback=None):
    """Normalize the weekday list without making daily rules ambiguous.

    ``scheduleWeekdays`` is meaningful only for a custom schedule.  Older
    records stored the weekday default alongside ``daily``; treating that
    stale list as an active restriction would make daily rules inconsistent,
    so daily is persisted and exposed as all seven days.
    """
    cycle = str(schedule_cycle or 'daily').strip().lower()
    if cycle == 'daily':
        return [1, 2, 3, 4, 5, 6, 7]
    days = parse_list_field(raw_value, fallback if fallback is not None else [1, 2, 3, 4, 5])
    return sorted({int(day) for day in days if str(day).isdigit() and 1 <= int(day) <= 7})

def normalize_target(row):
    row = dict(row)
    row['contentTypes'] = parse_list_field(row.get('contentTypes'), ['activities', 'changelogs'])
    row['triggerEvents'] = parse_list_field(row.get('triggerEvents'), [])
    row['customContent'] = row.get('customContent') or ''
    row['deliveryChannel'] = row.get('deliveryChannel') or 'group'
    row['cardTargetType'] = row.get('cardTargetType') or 'personal'
    row['cardConversationId'] = row.get('cardConversationId') or ''
    row['cardTemplateId'] = row.get('cardTemplateId') or ''
    row['cardRobotCode'] = row.get('cardRobotCode') or ''
    row['recipientName'] = row.get('recipientName') or ''
    row['recipientUserId'] = row.get('recipientUserId') or ''
    row['developer'] = canonical_developer_name(row.get('developer') or '')
    row['developerUserId'] = row.get('developerUserId') or ''
    row['targetType'] = row.get('targetType') or 'global'
    row['projectId'] = row.get('projectId') or ''
    row['requirementId'] = row.get('requirementId') or ''
    row['ownerUserId'] = row.get('ownerUserId') or ''
    row['ownerName'] = row.get('ownerName') or ''
    row['enabled'] = bool(row.get('enabled'))
    row['scheduleCycle'] = row.get('scheduleCycle') or 'daily'
    row['scheduleDay'] = int(row.get('scheduleDay') or 0)
    row['scheduleWeekdays'] = notification_weekday_values(row['scheduleCycle'], row.get('scheduleWeekdays'))
    row['contentRange'] = row.get('contentRange') or 'today'
    row['customRangeStart'] = row.get('customRangeStart') or ''
    row['customRangeEnd'] = row.get('customRangeEnd') or ''
    row['triggerType'] = row.get('triggerType') or 'schedule'
    row['reportScene'] = row.get('reportScene') or 'daily'
    if row['reportScene'] not in NOTIFICATION_REPORT_SCENES:
        row['reportScene'] = 'daily'
    row['lastSentAt'] = row.get('lastSentAt') or ''
    row['lastSendStatus'] = row.get('lastSendStatus') or ''
    row['lastSendError'] = row.get('lastSendError') or ''
    row['webhookMasked'] = (row.get('webhook') or '')[:32] + '...' if row.get('webhook') else ''
    return row

def target_range_label(target=None):
    target = target or {}
    mode = target.get('contentRange') or 'today'
    labels = {'today': '今日', 'last7days': '近 7 天', 'thisMonth': '本月', 'lastMonth': '上月'}
    if mode == 'custom':
        return f"{target.get('customRangeStart') or '今日'} 至 {target.get('customRangeEnd') or '今日'}"
    return labels.get(mode, '今日')

def notification_record_matches(target, row):
    """Apply the optional project/requirement/developer scope of a rule."""
    target = target or {}
    target_type = target.get('targetType') or 'global'
    if target_type == 'project' and target.get('projectId'):
        return str(row.get('projectId') or row.get('id') or '') == str(target.get('projectId'))
    if target_type == 'requirement' and target.get('requirementId'):
        return str(row.get('requirementId') or row.get('id') or '') == str(target.get('requirementId'))
    if target_type == 'developer' or target.get('developer'):
        developer = target.get('developer') or ''
        if not developer:
            return True
        candidates = [row.get('assignee'), row.get('requester'), row.get('devOwner'), row.get('recipientName')]
        return any((same_person_name(candidate, developer) for candidate in candidates if candidate))
    return True

def _notification_status_phrase(status, old_status='', new_status=''):
    normalized = LEGACY_STATUS_MAP.get(status or '', status or '')
    old_status = LEGACY_STATUS_MAP.get(old_status or '', old_status or '')
    new_status = LEGACY_STATUS_MAP.get(new_status or '', new_status or '')
    if normalized == '已上线':
        return '已完成上线'
    if normalized == '已交付':
        return '已完成交付'
    if normalized in ('已关闭', '已归档'):
        return '已完成归档'
    if old_status and new_status and (old_status != new_status):
        return f'由{STATUS_SHORT_LABELS.get(old_status, old_status)}推进至{STATUS_SHORT_LABELS.get(new_status, new_status)}'
    return STATUS_SHORT_LABELS.get(normalized, normalized or '进行中')

def notification_recipient_ids(target):
    target = target or {}
    values = str(target.get('recipientUserId') or '').replace('，', ',').split(',')
    ids = [value.strip() for value in values if value.strip()]
    if not ids and target.get('scope') == 'developer' and target.get('developerUserId'):
        ids = [str(target.get('developerUserId')).strip()]
    return list(dict.fromkeys(ids))

def notification_schedule_due(now, cycle='daily', schedule_day=0, schedule_weekdays=None):
    """Return whether a recurring notification is due on ``now``.

    The scheduler runs every 30 seconds.  Keep all recurring schedule
    semantics in this one helper so a rule configured as workdays/custom
    cannot accidentally fall back to daily delivery in another scheduler.
    ``once`` is intentionally excluded: one-off links are dispatched by the
    request flow itself.
    """
    cycle = str(cycle or 'daily').strip().lower()
    schedule_day = int(schedule_day or 0)
    if cycle == 'weekly':
        return now.isoweekday() == (schedule_day or 1)
    if cycle == 'monthly':
        return now.day == min(max(schedule_day or 1, 1), 31)
    if cycle in ('custom', 'workdays'):
        fallback = [1, 2, 3, 4, 5] if cycle == 'workdays' else []
        weekdays = set(notification_weekday_values('custom', schedule_weekdays, fallback=fallback))
        return now.isoweekday() in weekdays
    return cycle == 'daily'

def notification_schedule_key(now, cycle='daily'):
    cycle = str(cycle or 'daily').strip().lower()
    if cycle == 'weekly':
        return f'{now.isocalendar().year}-W{now.isocalendar().week:02d}'
    if cycle == 'monthly':
        return now.strftime('%Y-%m')
    return now.strftime('%Y-%m-%d')

def notification_event_detail(event_type, record):
    record = record or {}
    event_label = NOTIFICATION_EVENT_OPTIONS.get(event_type, '业务事件')
    title = record.get('title') or record.get('requirementTitle') or record.get('name') or '未命名事项'
    project = record.get('projectName') or record.get('pname') or ''
    details = [f'- 事件：{event_label}', f'- 事项：{title}']
    if project:
        details.append(f'- 所属项目：{project}')
    profile = l3_profile_text(record)
    if profile:
        details.append(f'- L3 工作属性：{profile}')
    if record.get('status'):
        details.append(f"- 当前状态：{record.get('status')}")
    if record.get('assignee'):
        details.append(f"- 开发负责人：{record.get('assignee')}")
    if record.get('recipientName'):
        details.append(f"- 待办接收人：{record.get('recipientName')}")
    return '### 即时业务事件\n' + '\n'.join(details)

def target_range(target, generated_at):
    target = target or {}
    mode = target.get('contentRange') or 'today'
    now = datetime.strptime(generated_at, '%Y-%m-%d %H:%M:%S')
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if mode == 'last7days':
        start, end = (today - timedelta(days=6), today + timedelta(days=1))
    elif mode == 'thisMonth':
        start = today.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    elif mode == 'lastMonth':
        this_month = today.replace(day=1)
        end = this_month
        start = (this_month - timedelta(days=1)).replace(day=1)
    elif mode == 'custom':
        start_text = target.get('customRangeStart') or today.strftime('%Y-%m-%d')
        end_text = target.get('customRangeEnd') or start_text
        try:
            start = datetime.strptime(start_text, '%Y-%m-%d')
            end = datetime.strptime(end_text, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            start, end = (today, today + timedelta(days=1))
    else:
        start, end = (today, today + timedelta(days=1))
    return (start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'))

def render_report(data, target, developer, generated_at):
    title = f'{developer}工作同步' if developer else '产品与工作同步'
    lines = [f'## {title}', f"> 同步时间：{generated_at[:16]}｜统计范围：{data['rangeLabel']}", '']
    lines.append('### 实际工作进展')
    if data['actualProgress']:
        for item in data['actualProgress']:
            link_title = f"[{item['title']}]({item['link']})" if item.get('link') else item['title']
            lines.append(f"- **{link_title}**｜{item['projectName']}：{item['content']}")
    else:
        lines.append('- 今日/本周期未登记新增工作进展。')
    lines.append('')
    lines.append('### 产品里程碑')
    if data['milestones']:
        for item in data['milestones']:
            link_title = f"[{item['title']}]({item['link']})" if item.get('link') else item['title']
            lines.append(f"- **{link_title}**｜{item['projectName']}：{item['text']}")
    else:
        lines.append('- 本统计周期无新的产品里程碑。')
    lines.append('')
    lines.append('### 当前在研产品')
    if data['activeProducts']:
        for item in data['activeProducts']:
            link_title = f"[{item['title']}]({item['link']})" if item.get('link') else item['title']
            latest = item.get('latestProgress') or {}
            latest_date = str(latest.get('workDate') or '')[:10]
            progress = f"；最近进展：{latest.get('content')}（{latest_date}）" if latest.get('content') else '；尚未登记工作进展'
            lines.append(f"- **{link_title}**｜{item['projectName']}｜{item['status']}第 {item['daysInProgress']} 天{progress}")
    else:
        lines.append('- 当前没有符合汇报口径的在研产品。')
    lines.append('')
    if (target or {}).get('customContent'):
        lines.extend(['### 补充说明', (target or {}).get('customContent'), ''])
    return '\n'.join(lines)
