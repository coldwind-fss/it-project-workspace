import hashlib


def stable_id(source_type, source_id, prefix='sa'):
    return prefix + hashlib.sha1(f'{source_type}:{source_id}'.encode('utf-8')).hexdigest()[:18]


def text(data, key, default=''):
    return str(data.get(key) or default).strip()


def projection(source, row, requirement):
    rid = requirement['id']
    kind = 'work_progress'
    title = row.get('logType') or '工作进展'
    content = row.get('content') or ''
    actor_id, actor = row.get('operatorUserId') or '', row.get('operatorName') or '系统'
    if source == 'work_log':
        kind = 'status_change' if content.startswith('状态更新为：') else {
            '遇到问题': 'issue', '交付说明': 'delivery', '验收确认': 'acceptance',
            '下一步': 'next_step', '工作进展': 'work_progress'}.get(title, 'work_progress')
    elif source == 'changelog':
        kind = 'status_change' if row.get('fieldName') == 'status' else 'work_progress'
        title = row.get('changeType') or '变更记录'
        content = f"{row.get('fieldName') or '字段'}：{row.get('oldValue') or '无'} → {row.get('newValue') or '无'}"
        if row.get('reason'):
            content += f"；原因：{row['reason']}"
        actor_id, actor = '', row.get('operator') or '系统'
    elif source == 'business_collaboration':
        kind, title, content = 'feedback', row.get('title') or '业务反馈', row.get('content') or ''
        actor_id, actor = row.get('requesterUserId') or '', row.get('requesterName') or '业务'
    return {'id': stable_id(source, row['id']), 'scopeType': 'requirement', 'scopeId': rid,
        'projectId': requirement.get('projectId') or '', 'requirementId': rid, 'activityType': kind,
        'title': title, 'content': content, 'actorUserId': actor_id, 'actorName': actor,
        'sourceType': source, 'sourceId': row['id'], 'createdAt': row.get('createdAt') or '',
        'updatedAt': (row.get('updatedAt') or '') if source=='business_collaboration' else row.get('createdAt') or '', 'deletedAt': ''}
