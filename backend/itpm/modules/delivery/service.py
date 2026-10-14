import json
from itpm.core.json_fields import object_field
from .public import DeliveryFacts
from .rules import FEEDBACK_TYPES,FEEDBACK_ROUTES
from itpm.core.errors import AppError


class Delivery(DeliveryFacts):
    def __init__(self,repo,clock,ids,v):
        super().__init__(repo.db)
        self.repo,self.clock,self.ids,self.v=repo,clock,ids,v
    def baselines(self,u,rid):return self.repo.find(u,'requirement_delivery_baselines',{'requirementId':rid},order=[('version',True),('createdAt',True)])
    def baseline(self,u,identifier):return self.repo.get(u,'requirement_delivery_baselines',identifier)
    def baseline_payload(self,row):
        if not row:return None
        return {**row,'content':object_field(row.get('content')),
            'statusLabel':{'draft':'草稿','pending_confirmation':'待业务确认','confirmed':'已确认','changes_requested':'业务要求修改','superseded':'已被新版本替代'}.get(row['status'],row['status'] or '未设置'),
            'templateLabel':self.v['DELIVERY_STANDARD_TEMPLATE_LABELS'].get(row.get('templateType'),row.get('templateType') or '通用交付标准'),'versionLabel':f"V{row.get('version') or 1}"}
    def materialize_confirmation(self,u,p,rid,confirmation,spec=None):
        if not rid or not confirmation or self.baselines(u,rid):return None,None
        content=object_field(confirmation.get('content'))
        for key,column in [('scope','usageScope'),('scenarios','businessProcess'),('expected','acceptanceCriteria')]:content[key]=content.get(key) or confirmation.get(column) or ''
        content.setdefault('evidence','');content.setdefault('exclusions','')
        if spec:content['parallelL3']={'title':spec.get('title') or '','scope':spec.get('scope') or '',
            'acceptanceDelta':spec.get('acceptanceDelta') or '','source':'demand_pool_confirmation'}
        template=self.v['DELIVERY_STANDARD_TEMPLATE_ALIASES'].get(confirmation.get('templateType') or 'custom',confirmation.get('templateType') or 'custom')
        now=self.clock.now();row={'id':self.ids.new('rdb',18),'requirementId':rid,'version':1,'templateType':template,
            'content':json.dumps(content,ensure_ascii=False),'status':'confirmed','recipientUserId':confirmation.get('recipientUserId') or '',
            'recipientName':confirmation.get('recipientName') or '','confirmationLinkId':'','supersedesId':'','sourceDemandConfirmationId':confirmation['id'],
            'createdByUserId':p.userId,'createdByName':p.name,'createdAt':now,'updatedAt':now,'confirmedAt':confirmation.get('confirmedAt') or now}
        self.repo.add(u,'requirement_delivery_baselines',row)
        summary='本次交付范围：'+content['scope']+'\n业务验证场景：'+content['scenarios']+'\n功能验收通过标准：'+content['expected']
        if spec:
            if spec.get('scope'):summary+='\n本独立 L3 工作项独有交付范围：'+spec['scope']
            if spec.get('acceptanceDelta'):summary+='\n本独立 L3 工作项验收补充：'+spec['acceptanceDelta']
        return row,summary[:10000]
    def links(self,u,rid):return self.repo.find(u,'collaboration_link_requests',{'requirementId':rid},order=[('rowid',True)])
    def link(self,u,identifier='',token='',lock=False):
        rows=self.repo.find(u,'collaboration_link_requests',{'token':token},lock=lock) if token else []
        return rows[0] if rows else self.repo.get(u,'collaboration_link_requests',identifier,lock=lock) if not token else None
    def add_link(self,u,row):self.repo.add(u,'collaboration_link_requests',row);return self.link(u,row['id'])
    def change_link(self,u,identifier,values):self.repo.change(u,'collaboration_link_requests',identifier,values);return self.link(u,identifier)
    def add_baseline(self,u,row):self.repo.add(u,'requirement_delivery_baselines',row);return self.baseline(u,row['id'])
    def change_baseline(self,u,identifier,values):self.repo.change(u,'requirement_delivery_baselines',identifier,values)
    def previous_key(self,u,rid,key):
        rows=self.repo.find(u,'collaboration_link_requests',{'requirementId':rid,'clientKey':key});return rows[0] if rows else None
    def revoke(self,u,rows):
        changed=[]
        for row in rows:
            current=self.link(u,row['id'],lock=True)
            if current and current['status']=='pending':
                self.change_link(u,row['id'],{'status':'revoked','revokedAt':self.clock.now()});changed.append(row)
        return changed
    def feedback(self,u,identifier='',round_id=''):
        rows=self.repo.find(u,'requirement_delivery_feedback',{'deliveryRoundId':round_id}) if round_id else []
        return rows[0] if rows else self.repo.get(u,'requirement_delivery_feedback',identifier) if not round_id else None
    def feedback_payload(self,row):
        return {**row,'feedbackTypeLabel':FEEDBACK_TYPES.get(row.get('feedbackType'),row.get('feedbackType') or '其他'),
            'routeTypeLabel':FEEDBACK_ROUTES.get(row.get('routeType'),row.get('routeType') or '待 IT 判断')} if row else None
    def add_feedback(self,u,row):self.repo.add(u,'requirement_delivery_feedback',row)
    def route_feedback(self,u,identifier,route,rid):
        self.repo.change(u,'requirement_delivery_feedback',identifier,{'routeType':route,'routedRequirementId':rid,
            'status':'created' if route.startswith('new_l3_') else 'routed','updatedAt':self.clock.now(),'resolvedAt':self.clock.now()})
        return self.feedback(u,identifier)
    def referenced_file(self,u,file):
        for row in self.repo.find(u,'collaboration_link_requests'):
            snapshot=object_field(row.get('snapshot'))
            if any(x.get('id')==file['id'] for x in snapshot.get('attachments',[]) if isinstance(x,dict)) or (
                row.get('responseMessageId') and row['responseMessageId']==file['ownerId'] and file['ownerType']=='collaboration_message'):return True
        return False
