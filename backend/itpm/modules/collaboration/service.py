"""Two-sided collaboration and stable read projections.

Own tables only; work/portfolio/identity/files are injected public capabilities.
GET projects history without creating rows. Write callers explicitly materialize.
"""
from dataclasses import replace
from itpm.core.errors import require
from itpm.modules.identity.public import split_people, same_name
from .rules import stable_id, projection, text


class CollaborationService:
    def __init__(self, repo, clock, ids, vocabulary, identity, work, portfolio, files, base):
        self.repo, self.clock, self.ids, self.v = repo, clock, ids, vocabulary
        self.identity, self.work, self.portfolio, self.files, self.base = identity, work, portfolio, files, base
    def source(self,u,table,identifier,active=False):
        return self.repo.get(u,table,identifier,active)
    def add_intake(self,u,row):
        self.repo.add(u,'business_intake_requests',row)
    def link_intake_work(self,u,identifier,req):
        self.repo.change(u,'business_intake_requests',identifier,{'requirementId':req['id'],'requirementTitle':req['title']})
    def change_thread(self,u,identifier,values):self.repo.change(u,'business_collaboration_items',identifier,values)
    def message(self,u,identifier):return self.repo.get(u,'business_collaboration_messages',identifier,True)
    def owners_for_requirement(self,u,rid):
        owners=[]
        for table,kind in [('shared_activities','shared_activity'),('shared_activity_comments','shared_activity_comment'),
            ('business_collaboration_items','collaboration'),('business_collaboration_messages','collaboration_message')]:
            for row in self.repo.find(u,table,{'requirementId':rid},active=kind!='collaboration'):owners.append((kind,row['id']))
        return owners

    def scope(self, u, kind, identifier):
        req = self.work.requirement(u, identifier) if kind != 'project' else None
        project = self.portfolio.project(u, identifier if kind == 'project' else (req or {}).get('projectId', ''))
        if kind != 'project' and req and not project and req.get('projectId'):
            archived=self.portfolio.raw_project(u,req['projectId'])
            if archived and archived.get('deletedAt'):req=None
        return project, req

    def visible(self, u, p, kind, identifier):
        project, req = self.scope(u, kind, identifier)
        if not p.authenticated or not (project if kind == 'project' else req):
            return False
        return p.role in {'admin', 'super_admin'} or bool(
            req and (self.identity.can_edit(u, p, req, 'requirement', project) or self.identity.matches(u, p, req.get('requester'))) or
            project and (self.identity.can_edit(u, p, project, 'project') or
                any(self.identity.matches(u, p, project.get(k)) for k in ['businessOwner', 'devOwner'])))

    def private(self, u, activity):
        if activity.get('sourceType') == 'work_log':
            source = self.work.log_source(u, activity.get('sourceId'))
            return bool(source and source.get('visibility') == 'it_private')
        return False

    def activity_visible(self, u, p, activity):
        if not self.visible(u, p, activity['scopeType'], activity['scopeId']):
            return False
        if self.private(u, activity):
            project, req = self.scope(u, activity['scopeType'], activity['scopeId'])
            return p.role in {'admin', 'super_admin'} or bool(req and self.identity.can_edit(u, p, req, 'requirement', project))
        return True

    def projected_messages(self, u, thread):
        rows = self.repo.find(u, 'business_collaboration_messages', {'collaborationId': thread['id']}, True,
            [('createdAt', False), ('rowid', False)])
        if rows:
            return rows
        side = 'business' if thread.get('direction') == 'business_to_it' else 'it'
        rows = []
        for prefix, content, at, kind, sender_side in [
            ('requester', thread.get('content') or thread.get('title'), thread.get('createdAt'),
                'issue' if thread.get('kind') == 'issue' else 'acceptance' if thread.get('kind') == 'acceptance' else 'message', side),
            ('recipient', thread.get('response'), thread.get('respondedAt') or thread.get('updatedAt'),
                'acceptance' if thread.get('status') in {'resolved', 'closed'} else 'message', 'it' if side == 'business' else 'business')]:
            if content:
                rows.append({'id': stable_id('legacy_message', thread['id'] + ':' + prefix, 'bcm'),
                    'collaborationId': thread['id'], 'requirementId': thread.get('requirementId') or '',
                    'senderUserId': thread.get(prefix + 'UserId') or '', 'senderName': thread.get(prefix + 'Name') or '',
                    'senderSide': sender_side, 'messageType': kind, 'content': content, 'createdAt': at or '',
                    'updatedAt': at or '', 'deletedAt': ''})
        return rows

    def historical(self, u, kind, identifier):
        project, req = self.scope(u, kind, identifier)
        reqs = self.work.requirements(u, project_id=identifier) if kind == 'project' else ([req] if req else [])
        persisted = self.repo.find(u, 'shared_activities', {'projectId' if kind == 'project' else 'requirementId': identifier})
        # Include tombstones in this map so a deleted historical projection stays deleted.
        by_id = {r['id']: r for r in persisted}
        for req in reqs:
            logs = self.work.log_sources(u, req['id'])
            for row in logs:
                if row.get('sourceBatchId') and any(x.get('sourceType') == 'manual' and x.get('sourceId') == row['sourceBatchId'] for x in by_id.values()):
                    continue
                item = projection('work_log', row, req)
                by_id.setdefault(item['id'], item)
            for row in self.work.changelogs(u, rid=req['id']):
                if row.get('fieldName') == 'status' and any(str(x.get('content') or '').startswith('状态更新为：' + str(row.get('newValue') or '')) for x in logs):
                    continue
                item = projection('changelog', row, req)
                by_id.setdefault(item['id'], item)
            for row in self.repo.find(u, 'business_collaboration_items', {'requirementId': req['id']}):
                item = projection('business_collaboration', row, req)
                by_id.setdefault(item['id'], item)
        return sorted([r for r in by_id.values() if not r.get('deletedAt')], key=lambda r: (r['createdAt'], r['id']), reverse=True)

    def activity(self, u, identifier):
        row = self.repo.get(u, 'shared_activities', identifier, True)
        if row:
            return row
        # Resolve slim source identities. Do not load every requirement's images
        # or replay every timeline just to authorize one historical comment.
        sources=self.work.projection_scopes(u)+[('business_collaboration',x['id'],x['requirementId']) for x in self.repo.projection_scopes(u)]
        for source,sid,rid in sources:
            if stable_id(source,sid)==identifier:
                return next((x for x in self.historical(u,'requirement',rid) if x['id']==identifier),None)
        return None

    def materialize(self, u, item):
        self.repo.add(u, 'shared_activities', item, conflict=['id'])
        if item.get('sourceType') == 'business_collaboration':
            thread = self.repo.get(u, 'business_collaboration_items', item['sourceId'])
            if thread:
                for msg in self.projected_messages(u, thread):
                    self.repo.add(u, 'business_collaboration_messages', {k: v for k, v in msg.items() if k != 'rowid'}, conflict=['id'])
                for row in self.projected_comments(u, item):
                    self.repo.add(u, 'shared_activity_comments', row, conflict=['id'])
        return self.repo.get(u, 'shared_activities', item['id'], True)

    def projected_comments(self, u, activity):
        rows = self.repo.find(u, 'shared_activity_comments', {'activityId': activity['id']}, True)
        by_id = {x['id']: x for x in rows}
        if activity.get('sourceType') == 'business_collaboration':
            thread = self.repo.get(u, 'business_collaboration_items', activity['sourceId'])
            for msg in self.projected_messages(u, thread)[1:] if thread else []:
                identifier = stable_id('business_message', msg['id'], 'sac')
                by_id.setdefault(identifier, {'id': identifier, 'activityId': activity['id'], 'projectId': activity['projectId'],
                    'requirementId': activity['requirementId'], 'commenterUserId': msg.get('senderUserId') or '',
                    'commenterName': msg.get('senderName') or '协作者', 'content': msg.get('content') or '',
                    'sourceType': 'business_message', 'sourceId': msg['id'], 'createdAt': msg.get('createdAt') or '',
                    'updatedAt': msg.get('updatedAt') or '', 'deletedAt': ''})
        return sorted(by_id.values(), key=lambda r: (r['createdAt'], r['id']))

    def comment_payload(self, u, row):
        attachments = self.files.list(u, 'shared_activity_comment', row['id'])
        if row.get('sourceType') == 'business_message':
            attachments += self.files.list(u, 'collaboration_message', row['sourceId'])
        return {**row, 'attachments': attachments}

    def activity_payload(self, u, row):
        attachments = self.files.list(u, 'shared_activity', row['id'])
        label = self.v['SHARED_ACTIVITY_TYPES'].get(row.get('activityType'), row.get('activityType') or '动态')
        if row.get('sourceType') == 'business_collaboration':
            thread = self.repo.get(u, 'business_collaboration_items', row['sourceId'])
            if thread:
                label = {'resource_request': '资料补充', 'acceptance': '业务协作'}.get(thread.get('kind'), label)
                attachments += self.files.list(u, 'collaboration', thread['id'])
                messages = self.projected_messages(u, thread)
                if messages:
                    attachments += self.files.list(u, 'collaboration_message', messages[0]['id'])
        comments = [self.comment_payload(u, c) for c in self.projected_comments(u, row)]
        return {**row, 'activityTypeLabel': label, 'attachments': attachments, 'comments': comments, 'commentCount': len(comments)}

    def activities(self, u, p, kind, identifier):
        require(self.visible(u, p, kind, identifier), '当前身份不是该需求的参与者' if kind == 'requirement' else '当前身份不是该产品的参与者', 403, 'FORBIDDEN')
        return [self.activity_payload(u, row) for row in self.historical(u, kind, identifier) if self.activity_visible(u, p, row)][:200]

    def create_activity(self, u, p, kind, identifier, d):
        require(self.visible(u, p, kind, identifier), '当前身份不是该需求的参与者' if kind == 'requirement' else '当前身份不是该产品的参与者', 403, 'FORBIDDEN')
        activity_type = text(d, 'activityType', 'work_progress')
        require(activity_type in self.v['SHARED_ACTIVITY_TYPES'], '不支持的动态类型')
        content = text(d, 'content')
        require(content, '动态内容不能为空')
        require(len(content) <= 10000, '动态内容最多10000字')
        project, req = self.scope(u, kind, identifier)
        aid, now = self.ids.new('sa', 18), self.clock.now()
        row = {'id': aid, 'scopeType': kind, 'scopeId': identifier, 'projectId': (project or {}).get('id') or '',
            'requirementId': (req or {}).get('id') or '', 'activityType': activity_type,
            'title': text(d, 'title', self.v['SHARED_ACTIVITY_TYPES'][activity_type]), 'content': content,
            'actorUserId': p.userId, 'actorName': p.name, 'sourceType': 'manual', 'sourceId': aid,
            'createdAt': now, 'updatedAt': now, 'deletedAt': ''}
        self.repo.add(u, 'shared_activities', row)
        return row, project, req

    def create_comment(self, u, p, identifier, content):
        row = self.activity(u, identifier)
        require(row, '共享动态不存在', 404, 'NOT_FOUND')
        require(self.activity_visible(u, p, row), '当前身份不是该动态的参与者', 403, 'FORBIDDEN')
        content = str(content or '').strip() or '补充附件'
        require(len(content) <= 10000, '评论最多10000字')
        self.materialize(u, row)
        now = self.clock.now()
        cid = self.ids.new('sac', 18)
        comment = {'id': cid, 'activityId': identifier, 'projectId': row['projectId'], 'requirementId': row['requirementId'],
            'commenterUserId': p.userId, 'commenterName': p.name, 'content': content, 'sourceType': 'manual', 'sourceId': cid,
            'createdAt': now, 'updatedAt': now, 'deletedAt': ''}
        self.repo.add(u, 'shared_activity_comments', comment)
        return comment, row

    def participant(self, p, row, prefix):
        return bool(p.userId and p.userId == row.get(prefix + 'UserId') or
            same_name(p.name or p.devOwnerName, row.get(prefix + 'Name'), self.v['DEVELOPERS']))

    def can_handle(self, u, p, row, intake=False):
        if not p.authenticated:
            return False
        if p.role in {'admin', 'super_admin'}:
            return True
        if intake:
            return p.role == 'editor' and row.get('assignee') in {'', '待分配', '未分配'} or bool(
                p.userId and p.userId == row.get('assigneeUserId') or self.identity.matches(u, p, row.get('assignee')))
        req = self.work.requirement(u, row.get('requirementId'))
        return bool(p.role == 'editor' and req and self.identity.can_edit(u, p, req, 'requirement') or
            any(self.participant(p, row, x) for x in ['requester', 'recipient']))

    def thread_visible(self, u, p, row, intake=False):
        if self.can_handle(u, p, row, intake):
            return True
        if intake:
            return self.participant(p, row, 'requester') or self.identity.matches(u, p, row.get('assignee'))
        req = self.work.requirement(u, row.get('requirementId'))
        return bool(req and self.identity.can_edit(u, p, req, 'requirement'))

    def message_side(self, u, p, row):
        requester, recipient = self.participant(p, row, 'requester'), self.participant(p, row, 'recipient')
        root = 'business' if row['direction'] == 'business_to_it' else 'it'
        if requester and not recipient:
            return root
        if recipient and not requester:
            return 'it' if root == 'business' else 'business'
        req = self.work.requirement(u, row.get('requirementId'))
        return 'it' if req and self.identity.can_edit(u, p, req, 'requirement') else root

    def message_payload(self, u, row):
        return {**row, 'messageTypeLabel': self.v['BUSINESS_COLLABORATION_MESSAGE_TYPES'].get(row.get('messageType'), row.get('messageType') or '讨论消息'),
            'attachments': self.files.list(u, 'collaboration_message', row['id'])}

    def thread_payload(self, u, p, row, messages=False, intake=False):
        kind = 'BUSINESS_INTAKE' if intake else 'BUSINESS_COLLABORATION'
        item = {**row, 'kindLabel': self.v[kind + '_KIND_LABELS'].get(row.get('kind'), row.get('kind') or '协作事项'),
            'statusLabel': self.v[kind + '_STATUS_LABELS'].get(row.get('status'), row.get('status') or '未设置'),
            'attachments': self.files.list(u, 'business_request' if intake else 'collaboration', row['id']),
            'requirementLink': self.base + '#/requirements/' + row['requirementId'] if row.get('requirementId') else '',
            'canHandle': self.can_handle(u, p, row, intake)}
        if intake:
            item['businessUrgencyLabel'] = self.v['BUSINESS_URGENCY_LABELS'].get(row.get('businessUrgency'), row.get('businessUrgency') or '一般事项')
        else:
            req = self.work.raw_requirement(u, row.get('requirementId'))
            project = self.portfolio.raw_project(u, (req or {}).get('projectId') or '')
            if req:
                item.update(requirementTitle=req['title'], projectId=req.get('projectId') or '', projectName=(project or {}).get('name') or req.get('projectName') or '')
            rows = self.projected_messages(u, row)
            if messages:
                item['messages'] = [self.message_payload(u, m) for m in rows]
            else:
                item['messageCount'] = len(self.repo.find(u, 'business_collaboration_messages', {'collaborationId': row['id']}, True))
        return item

    def list_threads(self, u, p, status='', rid='', intake=False):
        table = 'business_intake_requests' if intake else 'business_collaboration_items'
        rows = self.repo.find(u, table, {'requirementId': rid} if rid else {}, order=[('updatedAt', True), ('createdAt', True)] if rid else [('createdAt', True)], limit=None if rid else 500)
        if rid:
            require(self.work.requirement(u, rid), '需求不存在或已在回收站', 404, 'NOT_FOUND')
        return [self.thread_payload(u, p, row, bool(rid), intake) for row in rows
            if self.thread_visible(u, p, row, intake) and (not status or status == 'all' or row['status'] == status)]

    def insert_message(self, u, row, p, side, content, kind='message', at=None):
        mid, now = self.ids.new('bcm'), at or self.clock.now()
        message = {'id': mid, 'collaborationId': row['id'], 'requirementId': row.get('requirementId') or '',
            'senderUserId': p.userId, 'senderName': p.name, 'senderSide': side, 'messageType': kind,
            'content': content, 'createdAt': now, 'updatedAt': now, 'deletedAt': ''}
        self.repo.add(u, 'business_collaboration_messages', message)
        return self.repo.get(u, 'business_collaboration_messages', mid)

    def insert_thread(self, u, p, req, d, direction, recipient_name, recipient_id, business_id=''):
        now = self.clock.now()
        row = {'id': self.ids.new('bci'), 'requirementId': req['id'], 'businessRequestId': business_id,
            'direction': direction, 'kind': text(d, 'kind', 'clarification'),
            'status': text(d, 'status', 'waiting_business' if direction == 'it_to_business' else 'waiting_it'),
            'title': text(d, 'title'), 'content': text(d, 'content', text(d, 'description')),
            'requesterUserId': p.userId, 'requesterName': p.name, 'recipientUserId': recipient_id,
            'recipientName': recipient_name, 'dueDate': text(d, 'dueDate'), 'response': '',
            'sourceType': text(d, 'sourceType', 'in_app'), 'sourceRef': text(d, 'sourceRef'),
            'createdAt': now, 'updatedAt': now, 'respondedAt': '', 'closedAt': ''}
        self.repo.add(u, 'business_collaboration_items', row)
        message_type = 'issue' if row['kind'] == 'issue' else 'acceptance' if row['kind'] == 'acceptance' else 'message'
        self.insert_message(u, row, p, 'it' if direction == 'it_to_business' else 'business', row['content'] or row['title'], message_type, now)
        return self.repo.get(u, 'business_collaboration_items', row['id'])

    def create_thread(self, u, p, rid, d):
        project, req = self.scope(u, 'requirement', rid)
        require(req, '需求不存在或已在回收站', 404, 'NOT_FOUND')
        it = self.identity.can_edit(u, p, req, 'requirement', project)
        business = self.identity.has(u, p, 'business_request.submit') and (self.identity.matches(u, p, req.get('requester')) or project and self.identity.matches(u, p, project.get('businessOwner')))
        require(it or business, '只有 L3 负责人、业务提出方或管理员可以发起协作', 403, 'FORBIDDEN')
        kind, title, content = text(d, 'kind', 'clarification'), text(d, 'title'), text(d, 'content', text(d, 'description'))
        require(kind in self.v['BUSINESS_COLLABORATION_KIND_LABELS'], '不支持的协作事项类型')
        require(title and content, '协作事项标题和说明必填')
        require(len(title) <= 300 and len(content) <= 10000, '协作事项标题最多300字，说明最多10000字')
        names = split_people(req.get('requester') if it else req.get('assignee'))
        fallback = split_people((project or {}).get('businessOwner')) if it else []
        recipient = text(d, 'recipientName', (names or fallback or [''])[0])
        if not it:
            require(recipient not in {'', '待分配', '未分配'}, '当前 L3 还没有 IT 负责人，暂时无法发起业务协作')
        require(recipient, '请指定业务协作接收人')
        status = text(d, 'status', 'waiting_business' if it else 'waiting_it')
        require(status in self.v['BUSINESS_COLLABORATION_STATUS_LABELS'], '不支持的协作状态')
        return self.insert_thread(u, p, req, {**d, 'kind': kind, 'title': title, 'content': content, 'status': status},
            'it_to_business' if it else 'business_to_it', recipient, text(d, 'recipientUserId', self.identity.person_id(u, recipient))), req

    def get_thread(self, u, p, identifier, intake=False):
        row = self.repo.get(u, 'business_intake_requests' if intake else 'business_collaboration_items', identifier, lock=True)
        require(row, '业务协作提交不存在' if intake else '业务协作事项不存在', 404, 'NOT_FOUND')
        require(self.thread_visible(u, p, row, intake), '无权访问该业务协作事项', 403, 'FORBIDDEN')
        return row

    def update_thread(self, u, p, row, d, message=False):
        require(self.can_handle(u, p, row), '只有协作双方或管理员可以更新该事项', 403, 'FORBIDDEN')
        side = self.message_side(u, p, row)
        content = (text(d, 'content') or '补充附件') if message else str(d.get('response', d.get('handlerNote', row.get('response') or ''))).strip()
        kind = text(d, 'messageType', 'message')
        require(not message or kind in {'message', 'delivery', 'issue', 'acceptance'}, '不支持的协作消息类型')
        status = text(d, 'status', ('waiting_business' if side == 'it' else 'waiting_it') if message else row.get('status') or 'open')
        require(status in self.v['BUSINESS_COLLABORATION_STATUS_LABELS'], '不支持的协作状态')
        require(len(content) <= 10000, '协作消息最多10000字' if message else '协作回复最多10000字')
        require(status not in {'resolved', 'closed'} or content and content != '补充附件', '完成协作时必须填写回复或结果')
        changed = message or status != row.get('status') or content != (row.get('response') or '')
        msg = None
        if changed:
            # Materialize legacy initial messages only at the first actual write.
            for initial in self.projected_messages(u, row):
                self.repo.add(u, 'business_collaboration_messages', {k: v for k, v in initial.items() if k != 'rowid'}, conflict=['id'])
            now = self.clock.now()
            self.repo.change(u, 'business_collaboration_items', row['id'], {'status': status, 'response': content,
                'updatedAt': now, 'respondedAt': now if message or content != row.get('response') else row.get('respondedAt') or '',
                'closedAt': now if status in {'resolved', 'closed'} else ''})
            if content:
                msg = self.insert_message(u, row, p, side, content, kind if message else ('acceptance' if status in {'resolved', 'closed'} else 'message'))
        return self.repo.get(u, 'business_collaboration_items', row['id']), msg, changed

    def update_intake(self, u, p, row, d):
        require(self.can_handle(u, p, row, True), '只有管理员或当前负责人可以更新处理进度', 403, 'FORBIDDEN')
        status = text(d, 'status', row.get('status') or 'submitted')
        note = str(d.get('handlerNote', d.get('response', row.get('handlerNote') or ''))).strip()
        require(status in self.v['BUSINESS_INTAKE_STATUS_LABELS'], '不支持的处理状态')
        require(len(note) <= 10000, '处理反馈最多10000字')
        require(status not in {'resolved', 'rejected', 'closed'} or note, '完成或暂不处理时必须填写处理反馈')
        changed = status != row.get('status') or note != (row.get('handlerNote') or '')
        if changed:
            now = self.clock.now()
            self.repo.change(u, 'business_intake_requests', row['id'], {'status': status, 'handlerNote': note,
                'handledByUserId': p.userId, 'handledByName': p.name, 'updatedAt': now,
                'handledAt': now if status in {'resolved', 'rejected', 'closed'} else row.get('handledAt') or ''})
        return self.repo.get(u, 'business_intake_requests', row['id']), changed

    def link_intake_response(self, u, p, row, status, content, message):
        if row.get('businessRequestId') and (message or status in {'resolved', 'closed'}):
            now = self.clock.now()
            self.repo.change(u, 'business_intake_requests', row['businessRequestId'], {'status': status if status in {'resolved', 'closed'} else 'in_review',
                'handlerNote': content, 'handledByUserId': p.userId, 'handledByName': p.name, 'updatedAt': now,
                'handledAt': now if status in {'resolved', 'closed'} else ''})
