"""Pure V1 work report wording and grouping; explicit facts and time."""

from datetime import datetime,timedelta

import json

LEGACY_STATUS_MAP = {'active': '开发中', 'paused': '暂停中', 'archived': '已归档', '已排期': '已立项'}

STATUS_PROGRESS_LABELS = {'待处理': '等待处理', '进行中': '正在处理', '待交付': '等待交付', '已交付': '已完成交付', '已关闭': '已关闭', '待评估': '正在评估', '已立项': '已经立项', '需求确认中': '正在确认需求', '设计中': '正在设计', '开发中': '正在开发', '联调中': '正在联调', '测试中': '正在测试', '迭代中': '正在迭代', '待上线': '等待上线', '已上线': '已完成开发并上线', '维护中': '进入维护', '暂停中': '已暂停', '已关闭': '已关闭', '已归档': '已经归档'}

STATUS_SHORT_LABELS = {'待处理': '待处理', '进行中': '进行中', '待交付': '待交付', '已交付': '已交付', '已关闭': '关闭', '待评估': '评估', '已立项': '立项', '需求确认中': '需求确认', '设计中': '设计', '开发中': '开发', '联调中': '联调', '测试中': '测试', '迭代中': '迭代', '待上线': '待上线', '已上线': '已上线', '维护中': '维护', '暂停中': '暂停', '已关闭': '关闭', '已归档': '归档'}

COMPLETED_STATUSES = {'已交付', '已上线', '已关闭', '已归档'}

def status_progress_text(status):
    normalized = LEGACY_STATUS_MAP.get(status or '', status or '')
    return STATUS_PROGRESS_LABELS.get(normalized, f"状态为{normalized or '未设置'}")

def status_change_text(old_status, new_status):
    old_status = LEGACY_STATUS_MAP.get(old_status or '', old_status or '')
    new_status = LEGACY_STATUS_MAP.get(new_status or '', new_status or '')
    if new_status in ('已交付', '已上线'):
        return '今天已完成交付'
    if new_status == '已归档':
        return '今天已归档'
    if new_status == '已关闭':
        return '今天已关闭'
    if new_status == '进行中':
        return '进入处理中'
    return f"状态变更：从{STATUS_SHORT_LABELS.get(old_status or '', old_status or '未设置')}转入{STATUS_SHORT_LABELS.get(new_status or '', new_status or '未设置')}"

def l3_profile_text(row):
    """Describe an L3 record with the same product-lifecycle vocabulary used in the UI."""
    parts = []
    if row.get('type'):
        parts.append(str(row.get('type')))
    if row.get('changeObject'):
        parts.append(f"变更{row.get('changeObject')}")
    if row.get('impactLevel'):
        parts.append(f"{row.get('impactLevel')}影响")
    if row.get('workloadLevel'):
        parts.append(f"{row.get('workloadLevel')}工作量")
    return '·'.join(parts)

def _l3_progress_groups(new_reqs, status_changes):
    new_ids = {row.get('id') for row in new_reqs}
    latest_changes = {}
    for change in status_changes:
        rid = change.get('requirementId')
        if rid and rid not in latest_changes:
            latest_changes[rid] = change
    groups = {}
    for req in new_reqs:
        project = req.get('projectName') or '未关联项目'
        latest = latest_changes.get(req.get('id'))
        status = latest.get('newValue') if latest else req.get('status')
        groups.setdefault(project, []).append({'kind': 'new', 'title': req.get('title') or '未命名需求', 'status': status or '', 'text': f'新增工作记录，{status_progress_text(status)}' + (f'（{l3_profile_text(req)}）' if l3_profile_text(req) else '')})
    for rid, change in latest_changes.items():
        if rid in new_ids:
            continue
        project = change.get('projectName') or '未关联项目'
        groups.setdefault(project, []).append({'kind': 'changed', 'title': change.get('title') or change.get('requirementTitle') or '未命名需求', 'status': change.get('newValue') or '', 'text': status_change_text(change.get('oldValue') or '', change.get('newValue') or '') + (f'（{l3_profile_text(change)}）' if l3_profile_text(change) else '')})
    return [{'projectName': name, 'items': items} for name, items in sorted(groups.items(), key=lambda item: item[0])]

def project_changes(rows):
    changes, seen = ([], set())
    for row in rows:
        if row.get('entityId') in seen:
            continue
        try:
            before = json.loads(row.get('beforeValue') or '{}')
            after = json.loads(row.get('afterValue') or '{}')
        except (TypeError, json.JSONDecodeError):
            continue
        old_status, new_status = (before.get('status'), after.get('status'))
        if old_status != new_status and new_status:
            seen.add(row.get('entityId'))
            changes.append({'id': row.get('entityId'), 'name': row.get('entityName') or after.get('name') or '未命名项目', 'oldStatus': old_status or '', 'newStatus': new_status, 'text': status_change_text(old_status or '', new_status), 'createdAt': row.get('createdAt') or ''})
    return changes

def work_report(period, generated_at, new_projects, new_reqs, status_changes, project_changes):
    now = datetime.strptime(generated_at, '%Y-%m-%d %H:%M:%S')
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'month':
        start_dt = today.replace(day=1)
        label = f"本月（{start_dt.strftime('%m月%d日')}至{today.strftime('%m月%d日')}）"
        title = '本月工作记录'
    else:
        start_dt = today - timedelta(days=today.weekday())
        label = f"本周（{start_dt.strftime('%m月%d日')}至{today.strftime('%m月%d日')}）"
        title = '本周工作记录'
    end_dt = today + timedelta(days=1)
    start, end = (start_dt.strftime('%Y-%m-%d %H:%M:%S'), end_dt.strftime('%Y-%m-%d %H:%M:%S'))
    groups = _l3_progress_groups(new_reqs, status_changes)
    completed_ids = {row.get('requirementId') for row in status_changes if row.get('newValue') in COMPLETED_STATUSES}
    completed_ids.update({row.get('id') for row in new_reqs if row.get('status') in COMPLETED_STATUSES})
    lines = [f'## {title}', f'> 统计范围：{label}｜生成时间：{generated_at[:16]}', '']
    lines.append(f'- 新增 L2 项目：{len(new_projects)} 个')
    lines.append(f'- 新增 L3 需求：{len(new_reqs)} 条')
    lines.append(f'- 完成/归档 L3 需求：{len([rid for rid in completed_ids if rid])} 条')
    lines.append('')
    lines.append('### 新增 L2 项目')
    if new_projects:
        for project in new_projects:
            lines.append(f"- **{project.get('name') or '未命名项目'}**：{status_progress_text(project.get('status'))}")
    else:
        lines.append('- 无')
    lines.append('')
    lines.append('### L2 项目状态变化')
    if project_changes:
        for project in project_changes:
            lines.append(f"- **{project['name']}**，{project['text']}")
    else:
        lines.append('- 无')
    lines.append('')
    lines.append('### L2 项目下的 L3 工作记录')
    if groups:
        for group in groups:
            lines.append(f"#### {group['projectName']}")
            for index, item in enumerate(group['items'], 1):
                lines.append(f"{index}. **{item['title']}**，{item['text']}")
            lines.append('')
    else:
        lines.append('- 无新增或状态变化的 L3 需求')
    return {'period': period, 'title': title, 'rangeLabel': label, 'generatedAt': generated_at[:16], 'newProjects': new_projects, 'projectChanges': project_changes, 'groups': groups, 'summary': {'newProjects': len(new_projects), 'newRequirements': len(new_reqs), 'completedRequirements': len([rid for rid in completed_ids if rid]), 'statusChanges': len({row.get('requirementId') for row in status_changes if row.get('requirementId')}), 'projectStatusChanges': len(project_changes)}, 'markdown': '\n'.join(lines)}
