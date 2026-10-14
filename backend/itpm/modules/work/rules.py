from collections import Counter
from itpm.core.errors import require
from itpm.core.json_fields import object_field,list_field

TERMINAL={'已交付','已关闭','已上线','已归档','archived'}
LIST_FIELDS='id title type priority status projectId projectName sprintId assignee requester department description acceptanceCriteria expectedDeliveryTime completedAt storyPoints labels itemKind parentRequirementId versionTarget changeObject impactLevel workloadLevel createdByUserId createdByName createdAt updatedAt deletedAt deletedByUserId deletedByName'.split()
WEIGHTS={'待处理':0,'进行中':45,'待交付':90,'已交付':100,'已关闭':100,'待评估':0,'已排期':0,'已立项':0,'需求确认中':10,'设计中':20,'开发中':35,'迭代中':45,'联调中':60,'测试中':75,'验收中':85,'待上线':90,'维护中':100,'已上线':100,'已完成':100,'暂停中':0,'已归档':100,'active':35,'paused':0,'archived':100}

def progress(rows):
    if not rows:return {'total':0,'done':0,'progress':0,'currentTotal':0,'currentDone':0,'currentProgress':0,'mode':'empty','label':'暂无需求','subLabel':'先添加 L3 需求','statusCounts':{},'activeStatusCounts':{}}
    active=[x for x in rows if x.get('status') not in TERMINAL];done=len(rows)-len(active)
    value=round(sum(WEIGHTS.get(x.get('status'),0) for x in active)/len(active)) if active else 0
    mode=('iteration' if done else 'initial') if active else 'released'
    label=('持续迭代中' if done else '开发进度') if active else ('已上线' if any(x.get('status') in {'已上线','已归档','archived'} for x in rows) else '已交付')
    sub=f'当前迭代 {len(active)} 项' if active else '暂无新迭代'
    if any(x.get('status') in {'暂停中','paused'} for x in active):sub+=' · 有暂停项'
    return {'total':len(rows),'done':done,'progress':value if active else 100,'overallProgress':round(done/len(rows)*100),
        'currentTotal':len(active),'currentDone':sum(WEIGHTS.get(x.get('status'),0)>=100 for x in active),'currentProgress':value,'mode':mode,'label':label,'subLabel':sub,
        'statusCounts':dict(Counter(x.get('status') or '未设置' for x in rows)),'activeStatusCounts':dict(Counter(x.get('status') or '未设置' for x in active))}

def classification(data,v,creating=False):
    defaults={'type':'新增功能','status':'待处理','changeObject':'功能','impactLevel':'常规','workloadLevel':'中'}
    options={'type':v['REQUIREMENT_TYPE_OPTIONS'],'status':v['REQUIREMENT_STATUS_OPTIONS'],'changeObject':v['REQUIREMENT_CHANGE_OBJECT_OPTIONS'],'impactLevel':v['REQUIREMENT_IMPACT_OPTIONS'],'workloadLevel':v['REQUIREMENT_WORKLOAD_OPTIONS']}
    labels={'type':'工作类型','status':'状态','changeObject':'变更对象','impactLevel':'产品影响','workloadLevel':'工作量'}
    maps={'type':v['REQUIREMENT_TYPE_MAP'],'status':v['REQUIREMENT_STATUS_MAP'],'changeObject':v['REQUIREMENT_CHANGE_OBJECT_MAP']}
    result={}
    for k,default in defaults.items():
        if not creating and k not in data:continue
        val=data.get(k,default);require(val is not None and str(val).strip(),labels[k]+'不能为空')
        val=str(val).strip();val=maps.get(k,{}).get(val,val)
        require(val in options[k],labels[k]+'不合法，只能是：'+'、'.join(options[k]));result[k]=val
    return result

def transition(existing,target,reason,v,pending,delivered):
    require(str(reason or '').strip(),'状态变更必须填写调整说明')
    require(existing in v['REQUIREMENT_STATUS_OPTIONS'] or existing in v['REQUIREMENT_STATUS_MAP'],'无效状态流转')
    require(target in v['REQUIREMENT_STATUS_OPTIONS'] and target!=existing,'无效状态流转')
    if target=='待交付':require(pending,'请先在工作台完成交付卡并发送业务确认链接')
    if target=='已交付':require(delivered,'请先完成交付卡中的业务确认和上线登记')

def image_descriptors(identifier,images,base):
    return [{'id':x.get('id') or f'{identifier}-image-{i}','name':x.get('name') or '交付进度反馈截图','type':x.get('type') or 'image/*','existingIndex':i,'url':f'{base}api/requirements/{identifier}/attachments/{i}'} for i,image in enumerate(images) for x in [image if isinstance(image,dict) else {}]]

def phase_payload(row,v):
    labels={x['key']:x['label'] for x in v['PHASE_STATUS_OPTIONS']}
    return {**row,'required':bool(row.get('required')),'evidence':object_field(row.get('evidence')),'statusLabel':labels.get(row.get('status') or 'todo',row.get('status') or '待开始')}

def log_payload(row):
    return {'id':row.get('id'),'requirementId':row.get('requirementId'),'logType':row.get('logType') or '工作进展','content':row.get('content') or '',
        'operatorUserId':row.get('operatorUserId') or '','operatorName':row.get('operatorName') or '系统','createdAt':row.get('createdAt') or '',
        'occurredAt':row.get('occurredAt') or row.get('createdAt') or '','sourceBatchId':row.get('sourceBatchId') or '',
        'workDate':row.get('workDate') or (row.get('occurredAt') or '')[:10] or (row.get('createdAt') or '')[:10],
        'visibility':row.get('visibility') or 'it_private','sourceType':row.get('sourceType') or 'manual','sourceRef':row.get('sourceRef') or '',
        'reportingEligible':bool(row.get('reportingEligible')),'updatedAt':row.get('updatedAt') or row.get('createdAt') or ''}
