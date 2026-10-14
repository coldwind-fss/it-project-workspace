from dataclasses import replace
from itpm.core.errors import require
from itpm.core.events import AfterCommitAction
from itpm.modules.collaboration.public import text


class CollaborationWorkflow:
    def __init__(self, service, project_work, files):
        self.service, self.flow, self.files = service, project_work, files

    def shared_todo(self, u, p, activity, project, req, message):
        if not req:
            return
        f = self.flow
        side_it = f.identity.can_edit(u, p, req, 'requirement', project)
        recipient = ((project or {}).get('businessOwner') or req.get('requester')) if side_it else (req.get('assignee') or (project or {}).get('devOwner'))
        same_actor = recipient == p.name or bool(p.userId and f.identity.person_id(u, recipient) == p.userId)
        if recipient and recipient not in {'待分配', '未分配'} and not same_actor:
            f.inbox.assign(u, p, req, message, [recipient], {}, 'shared_activity')

    def shared(self, u, p, kind, identifier, d):
        f, s = self.flow, self.service
        f.identity.authenticated(p)
        row, project, req = s.create_activity(u, p, kind, identifier, d)
        if req:
            f.work.collaboration_log(u, p, req['id'], f.v['SHARED_ACTIVITY_LOG_TYPES'].get(row['activityType'], '工作进展'), row['content'], row['id'])
            self.shared_todo(u, p, row, project, req, p.name + '发布了' + f.v['SHARED_ACTIVITY_TYPES'][row['activityType']])
        f.audit.record(u, p, 'L3' if req else 'L2', identifier, (req or project).get('title') or (req or project).get('name') or identifier,
            'shared_activity', '发布' + f.v['SHARED_ACTIVITY_TYPES'][row['activityType']], after={'activityId': row['id'], 'activityType': row['activityType']})
        event = {**(project or {}), **(req or {}), 'projectId': row['projectId'], 'projectName': (project or {}).get('name') or '',
            'scopeType': kind, 'scopeId': identifier, 'activityId': row['id'], 'activityTypeLabel': f.v['SHARED_ACTIVITY_TYPES'][row['activityType']],
            'content': row['content'], 'actorName': p.name}
        f.emit(u, p, 'shared_activity_created', event, kind)
        return s.activity_payload(u, row)

    def comment(self, u, p, identifier, content):
        f, s = self.flow, self.service
        f.identity.authenticated(p)
        row, activity = s.create_comment(u, p, identifier, content)
        project, req = s.scope(u, activity['scopeType'], activity['scopeId'])
        if req:
            self.shared_todo(u, p, activity, project, req, p.name + '评论了共享动态')
        target = req or project or {}
        f.audit.record(u, p, 'L3' if req else 'L2', target.get('id') or activity['projectId'], target.get('title') or target.get('name') or '',
            'shared_activity_comment', '评论共享动态', after={'activityId': identifier, 'commentId': row['id']})
        event = {**(project or {}), **(req or {}), 'projectId': activity['projectId'], 'projectName': (project or {}).get('name') or '',
            'scopeType': activity['scopeType'], 'scopeId': activity['scopeId'], 'activityId': identifier,
            'commentId': row['id'], 'title': '共享动态评论', 'content': row['content'], 'actorName': p.name}
        f.emit(u, p, 'shared_activity_comment_created', event, activity['scopeType'])
        return s.comment_payload(u, row)

    def create_thread(self, u, p, rid, d):
        f, s = self.flow, self.service
        f.identity.authenticated(p)
        row, req = s.create_thread(u, p, rid, d)
        f.audit.record(u, p, 'L3', req['id'], req['title'], 'business_collaboration_create', '发起业务协作事项',
            after={'businessCollaborationId': row['id'], 'title': row['title'], 'recipientName': row['recipientName'], 'direction': row['direction']})
        f.inbox.collaboration_todo(u, p, row, req)
        return s.thread_payload(u, p, row, True)

    def update_thread(self, u, p, identifier, d, message=False):
        f, s = self.flow, self.service
        f.identity.authenticated(p)
        old = s.get_thread(u, p, identifier)
        row, msg, changed = s.update_thread(u, p, old, d, message)
        project, req = s.scope(u, 'requirement', row['requirementId'])
        if changed:
            content, status = row['response'], row['status']
            if req and content:
                kind = {'delivery': '交付说明', 'issue': '遇到问题', 'acceptance': '验收确认'}.get(d.get('messageType'), '工作进展') if message else ('交付说明' if status in {'resolved', 'closed'} else '工作进展')
                f.work.collaboration_log(u, p, req['id'], kind, ('业务协作：' if message else '业务协作回复：') + content)
                after = {'businessCollaborationId': identifier, 'status': status}
                after['messageType' if message else 'response'] = d.get('messageType') or 'message' if message else content
                f.audit.record(u, p, 'L3', req['id'], req['title'], 'business_collaboration_message' if message else 'business_collaboration_update',
                    '发送业务协作消息' if message else '更新业务协作回复', after=after)
            if status in {'resolved', 'closed'}:
                for todo in f.inbox.close_collaboration(u, identifier):
                    if todo.get('dingTalkSent') and todo.get('dingTalkTaskId'):
                        u.events.append(AfterCommitAction(lambda todo=todo: f.notices.complete_native(todo)))
            elif message:
                side = s.message_side(u, p, old)
                root_side = 'business' if old['direction'] == 'business_to_it' else 'it'
                prefix = 'recipient' if side == root_side else 'requester'
                f.inbox.collaboration_todo(u, p, {**old, 'recipientUserId': old.get(prefix + 'UserId') or '',
                    'recipientName': old.get(prefix + 'Name') or '', 'content': content}, req)
            elif status == 'waiting_it' and content and s.participant(p, old, 'recipient'):
                f.inbox.collaboration_todo(u, p, {**old, 'id': '', 'recipientUserId': old.get('requesterUserId') or '',
                    'recipientName': old.get('requesterName') or '', 'content': '业务已回复，请继续处理：' + content}, req)
            s.link_intake_response(u, p, old, status, content, message)
        result = s.thread_payload(u, p, row, message)
        if message:
            result['messageId'] = (msg or {}).get('id') or ''
        return result

    def intake(self, u, p, d, webhook=False):
        f, s = self.flow, self.service
        if not webhook:
            f.identity.action(u, p, 'business_request.submit')
        kind = text(d, 'kind', 'new_requirement')
        require(kind in f.v['BUSINESS_INTAKE_KIND_LABELS'], '不支持的业务协作类型')
        feedback = text(d, 'originalFeedback', text(d, 'content', text(d, 'description')))
        require(feedback, '请填写需求内容或反馈')
        require(len(feedback) <= 10000, '需求内容最多10000字')
        req, project = None, None
        pid = text(d, 'projectId')
        if kind != 'new_requirement':
            rid = text(d, 'requirementId')
            require(rid, '该类型必须选择关联需求')
            project, req = s.scope(u, 'requirement', rid)
            require(req, '关联需求不存在或已在回收站', 404, 'NOT_FOUND')
            require(not pid or pid == req.get('projectId'), '关联需求不属于所选项目')
            pid = req.get('projectId') or ''
        if pid:
            project = f.portfolio.project(u, pid)
            require(project, '所属项目不存在或已在回收站')
        title = text(d, 'title', (req or {}).get('title') or '')
        require(title, '标题必填')
        require(len(title) <= 300, '标题最多300字')
        requester = text(d, 'requesterName', p.name)
        require(requester, '提出人不能为空')
        actor = replace(p, name=requester, userId=text(d, 'requesterUserId', p.userId))
        assignee = (req or {}).get('assignee') or (project or {}).get('devOwner') or text(d, 'assignee', '待分配')
        priority = text(d, 'priority', (req or {}).get('priority') or 'P2')
        priority = priority if priority in {'P0', 'P1', 'P2', 'P3', 'P4'} else 'P2'
        urgency = text(d, 'businessUrgency', 'normal')
        urgency = urgency if urgency in f.v['BUSINESS_URGENCY_LABELS'] else 'normal'
        now = f.clock.now()
        row = {'id': f.ids.new('bir'), 'kind': kind, 'status': 'submitted', 'title': title, 'originalFeedback': feedback,
            'requesterUserId': actor.userId, 'requesterName': actor.name, 'department': text(d, 'department', (req or {}).get('department') or (project or {}).get('department') or ''),
            'projectId': pid, 'projectName': (project or {}).get('name') or '', 'requirementId': (req or {}).get('id') or '',
            'requirementTitle': (req or {}).get('title') or title, 'assignee': assignee,
            'assigneeUserId': text(d, 'assigneeUserId', f.identity.person_id(u, assignee)),
            'expectedDeliveryTime': text(d, 'expectedDeliveryTime', (req or {}).get('expectedDeliveryTime') or ''),
            'priority': priority, 'businessUrgency': urgency, 'sourceType': text(d, 'sourceType', 'dingtalk_webhook' if webhook else 'in_app')[:80],
            'sourceRef': text(d, 'sourceRef')[:300], 'handlerNote': '', 'handledByUserId': '', 'handledByName': '',
            'createdAt': now, 'updatedAt': now, 'handledAt': ''}
        s.add_intake(u, row)
        notify = bool(d.get('notify')) and not webhook
        if not req:
            req = f.work.legacy_intake(u, actor, row, project)
            enriched = {**req, 'pname': (project or {}).get('name'), 'images': []}
            f.audit.record(u, actor, 'L3', req['id'], title, 'create', '业务协作提交新需求', after=enriched)
            if notify:f.assign_todos(u,actor,enriched,'业务协作者提交了新需求，请确认处理')
            else:f.inbox.assign(u, actor, enriched, '业务协作者提交了新需求，请确认处理', [assignee], f.identity.policy(u))
            if notify:
                f.emit(u, actor, 'requirement_created', enriched, 'requirement')
                f.emit(u, actor, 'requirement_assigned', enriched, 'requirement')
        else:
            thread = s.insert_thread(u, actor, req, {'kind': {'issue': 'issue', 'delivery_confirmation': 'acceptance'}.get(kind, 'business_feedback'),
                'status': 'waiting_it', 'title': title, 'content': feedback, 'dueDate': row['expectedDeliveryTime'],
                'sourceType': row['sourceType'], 'sourceRef': row['sourceRef']}, 'business_to_it', assignee, row['assigneeUserId'], row['id'])
            f.work.collaboration_log(u, actor, req['id'], {'issue': '遇到问题', 'delivery_confirmation': '交付说明'}.get(kind, '工作进展'), '业务协作提交：' + feedback)
            f.audit.record(u, actor, 'L3', req['id'], req['title'], 'business_feedback', '业务协作者提交' + f.v['BUSINESS_INTAKE_KIND_LABELS'][kind],
                after={'businessRequestId': row['id'], 'requirementId': req['id'], 'content': feedback})
            f.inbox.collaboration_todo(u, actor, thread, req)
            if notify:
                f.emit(u, actor, 'todo_created', {**req, 'message': feedback}, 'requirement')
        s.link_intake_work(u, row['id'], req)
        return s.thread_payload(u, p, s.source(u, 'business_intake_requests', row['id']), intake=True)

    def update_intake(self, u, p, identifier, d):
        f, s = self.flow, self.service
        f.identity.authenticated(p)
        old = s.get_thread(u, p, identifier, True)
        row, changed = s.update_intake(u, p, old, d)
        if changed and row.get('requirementId') and row.get('handlerNote'):
            f.work.collaboration_log(u, p, row['requirementId'], '交付说明' if row['status'] in {'resolved', 'closed'} else '工作进展', '业务协作处理反馈：' + row['handlerNote'])
            f.audit.record(u, p, 'L3', row['requirementId'], row.get('requirementTitle') or row['title'], 'business_request_update',
                '更新业务协作处理反馈', after={'businessRequestId': identifier, 'status': row['status'], 'handlerNote': row['handlerNote']})
        return s.thread_payload(u, p, row, intake=True)

    def personal_action(self, u, p, identifier, done=False):
        f = self.flow
        f.identity.authenticated(p)
        before, after = f.inbox.personal_action(u, p, identifier, done)
        if done:
            if before.get('dingTalkTaskId'):
                u.events.append(AfterCommitAction(lambda: f.notices.complete_native(before)))
            f.audit.record(u, p, 'TODO', identifier, before.get('requirementTitle') or identifier, 'done', '完成个人待办', before, after)
        return after

    def owner_visible(self, u, p, kind, identifier, materialize=False):
        s = self.service
        if kind in {'shared_activity', 'shared_activity_comment'}:
            row = s.activity(u, identifier) if kind == 'shared_activity' else s.source(u, 'shared_activity_comments', identifier, True)
            activity = row if kind == 'shared_activity' else s.activity(u, (row or {}).get('activityId') or '')
            allowed = bool(row and activity and s.activity_visible(u, p, activity))
            if allowed and materialize:
                s.materialize(u, activity)
            return allowed
        if kind == 'business_request':
            row = s.source(u, 'business_intake_requests', identifier)
            return bool(row and s.thread_visible(u, p, row, True))
        if kind in {'collaboration', 'collaboration_message'}:
            row = s.source(u, 'business_collaboration_items' if kind == 'collaboration' else 'business_collaboration_messages', identifier)
            thread = row if kind == 'collaboration' else s.source(u, 'business_collaboration_items', (row or {}).get('collaborationId') or '')
            return bool(row and thread and s.thread_visible(u, p, thread))
        return False
