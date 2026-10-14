from itpm.core.errors import require
from itpm.core.json_fields import object_field,list_field

RECORD_TYPES=[{'key':'poc','label':'POC 验证'},{'key':'ai_capability','label':'AI 能力'}]
STATUSES=[{'key':'draft','label':'草稿'},{'key':'planned','label':'待开始'},{'key':'in_progress','label':'进行中'},{'key':'completed','label':'已完成'},{'key':'archived','label':'已归档'}]
CONCLUSIONS=[{'key':'passed','label':'通过'},{'key':'partial','label':'部分通过'},{'key':'failed','label':'未通过'},{'key':'unknown','label':'暂无法判断'},{'key':'documented','label':'已沉淀'}]
TEXT_FIELDS='ownerUserId ownerName projectId projectName requirementId requirementTitle demandId demandTitle sourceType sourceRef derivedFromId objective hypothesis scope sampleData method successCriteria result limitations nextSteps modelName modelVersion promptOrApproach reuseGuidance artifactType'.split()

def values(data,old,p,now,identifier):
    record_type=str(data.get('recordType') or old.get('recordType') or 'poc').strip()
    status=str(data.get('status') or old.get('status') or 'draft').strip()
    title=str(data.get('title') or old.get('title') or '').strip()[:200]
    conclusion=str(data.get('conclusion') if 'conclusion' in data else old.get('conclusion') or '').strip()
    require(record_type in {x['key'] for x in RECORD_TYPES},'记录类型不合法')
    require(title,'请输入记录名称');require(status in {x['key'] for x in STATUSES},'记录状态不合法')
    require(not conclusion or conclusion in {x['key'] for x in CONCLUSIONS},'验证结论不合法')
    require(status!='completed' or conclusion,'完成记录前请选择验证结论')
    defaults={'ownerUserId':p.userId,'ownerName':(p.devOwnerName or p.name),'sourceType':'manual','artifactType':'text'}
    limits={**dict.fromkeys('ownerUserId ownerName projectId requirementId demandId derivedFromId modelVersion'.split(),120),
        **dict.fromkeys('projectName requirementTitle demandTitle modelName'.split(),200),'sourceType':60,'sourceRef':300,'artifactType':40}
    row={k:str((data.get(k) if k in data else old.get(k,defaults.get(k,''))) or '').strip()[:limits.get(k,10000)] for k in TEXT_FIELDS}
    row.update(id=identifier,recordType=record_type,title=title,status=status,conclusion=conclusion,
        metrics=object_field(data.get('metrics') if 'metrics' in data else old.get('metrics')),
        tags=list_field(data.get('tags') if 'tags' in data else old.get('tags')),
        createdByUserId=old.get('createdByUserId') or p.userId,createdByName=old.get('createdByName') or (p.devOwnerName or p.name),
        createdAt=old.get('createdAt') or now,updatedAt=now,
        completedAt=now if status=='completed' else '' if old.get('status')=='completed' else old.get('completedAt') or '',
        archivedAt=now if status=='archived' else '')
    return row

def labels(row):
    row=dict(row)
    for field,options in [('recordType',RECORD_TYPES),('status',STATUSES),('conclusion',CONCLUSIONS)]:
        row[field+'Label']=next((x['label'] for x in options if x['key']==row.get(field)),row.get(field) or '')
    source=row.get('sourceType') or ''
    row['sourceLabel']={'manual':'手工创建','development':'开发过程创建','demand_pool':'需求池 POC','derived_from_poc':'由 POC 沉淀'}.get(source,source or '手工创建')
    row.update(metrics=object_field(row.get('metrics')),tags=list_field(row.get('tags')))
    return row
