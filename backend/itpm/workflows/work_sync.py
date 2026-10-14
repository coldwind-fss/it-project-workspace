import json
from itpm.core.errors import require,AppError
from itpm.modules.work_sync.public import WORK_SYNC_SERVICE_USER_ID,WORK_SYNC_SERVICE_NAME

class SyncWorkflow:
    def __init__(self,sync,flow):self.sync,self.flow=sync,flow
    def intake(self,u,p,data):
        sync,flow=self.sync,self.flow;project=sync.project(u,data);mode,source,items,key=sync.normalize(p,data,project)
        if mode=='commit' and p.role!='work_sync_service':flow.identity.action(u,p,'requirement.create')
        if mode=='commit':
            replay=sync.replay(u,p,key,data,project)
            if replay:return replay
            u.lock_key('work-sync-project',project['id'])
        preview=sync.preview(u,project,items)
        if mode=='preview':return sync.result(project,'',key,source,preview,'preview')
        if any(r['action']=='needs_review' for r in preview):raise AppError('存在同名记录，需在预览中确认后改为 append 或更换标题',409,safe_details=sync.result(project,'',key,source,preview,'needs_review'))
        bid=sync.begin(u,p,key,data,project,source);results=[]
        for index,(item,checked) in enumerate(zip(items,preview)):
            action=checked['action'];rid=checked['existingRequirementId'];logs=0
            if action=='create':
                req=flow.work.sync_create(u,p,item,project);rid=req['id']
                flow.audit.record(u,p,'L3',rid,item['title'],'create','通用开发工作同步写入',after={'id':rid,'title':item['title'],'projectId':project['id'],'sourceBatchId':bid},source_batch_id=bid)
                for log in item['logs']:logs+=int(flow.work.sync_log(u,p,rid,log,bid))
                if data.get('notify'):
                    flow.assign_todos(u,p,req,'通用开发同步新增，请确认处理');flow.emit(u,p,'requirement_created',{**req,'pname':project.get('name')},'requirement')
            elif action=='append':
                for log in item['logs']:logs+=int(flow.work.sync_log(u,p,rid,log,bid,True))
                if logs:flow.audit.record(u,p,'L3',rid,item['title'],'work_log','通用开发工作同步追加动态',after={'requirementId':rid,'logsAdded':logs,'sourceBatchId':bid},source_batch_id=bid)
            sync.add_item(u,bid,index,action,item,rid)
            results.append({'index':index,'action':action,'title':item['title'],'requirementId':rid,'logsAdded':logs,
                'link':flow.notices.base+'/#/requirements/'+rid if rid else ''})
        result=sync.result(project,bid,key,source,results,'committed');sync.finish(u,bid,result);return result
    def rollback(self,u,p,bid):
        sync,flow=self.sync,self.flow;batch=sync.batch(u,bid,True);require(batch,'同步批次不存在',404,'NOT_FOUND')
        if p.role=='work_sync_service':require(batch['operatorUserId']==WORK_SYNC_SERVICE_USER_ID,'工作同步服务只能撤回自己创建的批次',403,'FORBIDDEN')
        else:flow.identity.action(u,p,'requirement.delete')
        if batch['status']=='rolled_back':return dict(batchId=bid,status='rolled_back',removedRequirements=0,removedLogs=0)
        require(batch['status']=='committed','只有已提交批次可以撤回')
        items=sync.items(u,bid);rids=[x['requirementId'] for x in items if x['action']=='create' and x['requirementId']]
        require(not sync.manual_after(u,bid,[x['requirementId'] for x in items if x['requirementId']]),'该批次包含后续人工操作，请保留记录并人工处理，不能直接撤回',409,'MANUAL_FOLLOWUP')
        removed,logs=flow.work.sync_rollback(u,p,rids,bid)
        for rid in rids:flow.inbox.purge_for_work(u,rid)
        flow.audit.purge_batch(u,bid);result=dict(batchId=bid,status='rolled_back',removedRequirements=removed,removedLogs=logs);sync.finish(u,bid,result,True);return result
    def correct(self,u,p,data):
        require(p.role=='work_sync_service','负责人修正仅允许工作同步服务处理自己创建的记录',403,'FORBIDDEN')
        ids=data.get('requirementIds');require(isinstance(ids,list) and ids,'requirementIds 必须是非空数组')
        ids=[str(x or '').strip() for x in ids];require(all(ids),'requirementIds 不能包含空值');require(len(ids)<=100,'单次最多修正100条记录');require(len(set(ids))==len(ids),'requirementIds 不能重复')
        developer=str(data.get('developerOwner') or data.get('assignee') or '').strip();business=str(data.get('businessOwner') or data.get('requester') or '').strip()
        require(developer and business,'developerOwner 和 businessOwner 必填');require(len(developer)<=120 and len(business)<=120,'负责人名称最多120字')
        require(WORK_SYNC_SERVICE_NAME not in {developer,business},'负责人不能填写接口服务身份');rows=[]
        for rid in ids:
            row=self.flow.work.requirement(u,rid);require(row,'记录不存在或已删除：'+rid,404,'NOT_FOUND')
            require(not data.get('projectId') or row['projectId']==data['projectId'],'记录不属于指定项目：'+rid,409,'CONFLICT')
            require(row.get('createdByUserId')==WORK_SYNC_SERVICE_USER_ID or row.get('createdByName')==WORK_SYNC_SERVICE_NAME,'工作同步服务不能修正非自己创建的记录：'+rid,403,'FORBIDDEN');rows.append(row)
        updated=[];unchanged=[];reason=str(data.get('reason') or '修正工作同步记录的真实负责人').strip()[:500]
        for row in rows:
            if row.get('assignee')==developer and row.get('requester')==business:unchanged.append(row['id']);continue
            self.flow.work.sync_correct(u,p,row,developer,business,reason)
            self.flow.audit.record(u,p,'L3',row['id'],row.get('title') or row['id'],'owner_update',reason,before={k:row.get(k) or '' for k in ['assignee','requester']},after={'assignee':developer,'requester':business,'ownerCorrection':True});updated.append(row['id'])
        return {'status':'updated' if updated else 'unchanged','developerOwner':developer,'businessOwner':business,'updatedRequirementIds':updated,'unchangedRequirementIds':unchanged,'auditCreatorUnchanged':True}
