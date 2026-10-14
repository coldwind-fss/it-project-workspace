import json
import math
import re
from itpm.core.errors import require

TRANSITIONS={
 'pending_evaluation':{'evaluating','awaiting_supplement','business_review','review_complete','poc','deferred','not_implemented','merged','ordinary_task'},
 'evaluating':{'awaiting_supplement','business_review','review_complete','poc','deferred','not_implemented','merged','ordinary_task'},
 'awaiting_supplement':{'evaluating','business_review','review_complete','deferred','not_implemented'},
 'business_review':{'review_complete','awaiting_confirmation','poc','deferred','not_implemented','merged','ordinary_task','evaluating'},
 'review_complete':{'awaiting_confirmation','poc','deferred','not_implemented','merged','ordinary_task'},
 'poc':{'review_complete','awaiting_confirmation','deferred','not_implemented'},
 'awaiting_confirmation':{'business_confirmed','evaluating'},'business_confirmed':{'ready_for_l3','converted'},
 'ready_for_l3':{'converted'},'deferred':{'evaluating','pending_evaluation'},'not_implemented':{'evaluating'},
 'merged':set(),'ordinary_task':set(),'converted':set()}


def text(d,key,default='',limit=None):
    value=str(d.get(key) or default).strip()
    return value[:limit] if limit else value


def answers(data):
    value=data.get('answers') if isinstance(data.get('answers'),dict) else data
    result={}
    for key,value in value.items():
        if isinstance(key,str) and len(str(value or '').strip())<=5000:
            result[key[:80]]=str(value or '').strip()
    return result


def confirmation_content(raw,data=None,legacy=None):
    raw=raw if isinstance(raw,dict) else {};data=data or {};legacy=legacy or {}
    content={str(k).strip()[:160]:str(v or '').strip()[:10000] for k,v in raw.items()
        if str(k).strip() and k!='valueDefinition' and not isinstance(v,(dict,list))}
    for key,column in [('scope','usageScope'),('scenarios','businessProcess'),('expected','acceptanceCriteria')]:
        content[key]=content.get(key) or text(data,column,text(legacy,column),10000)
    content.setdefault('evidence','');content.setdefault('exclusions','');content['contentSchemaVersion']='confirmation-v2'
    definition=raw.get('valueDefinition')
    if isinstance(definition,dict):
        result={k:text(definition,k,'outcome' if k=='verificationMode' else '',limit) for k,limit in
            [('verificationMode',40),('baselineSummary',10000),('expectedSummary',10000),('metricOwnerName',120),('metricOwnerUserId',120),('nonQuantifiableReason',3000)]}
        result['metrics']=[]
        for metric in definition.get('metrics',[])[:20] if isinstance(definition.get('metrics'),list) else []:
            if not isinstance(metric,dict):continue
            clean={k:str(metric[k]).strip()[:160] for k in ['key','label','unit','measurementWindow','source','direction'] if metric.get(k) is not None and str(metric[k]).strip()}
            for k in ['baselineValue','targetValue']:
                value=metric.get(k)
                if value is not None and not isinstance(value,(list,dict,bool)) and str(value).strip():clean[k]=str(value).strip()[:80]
            if clean:result['metrics'].append(clean)
        content['valueDefinition']=result
    return content


def validate_confirmation(content,required=True):
    require(text(content,'expected'),'请先填写功能验收通过标准')
    definition=content.get('valueDefinition')
    require(not required or isinstance(definition,dict),'请先填写上线前价值验证口径')
    if not isinstance(definition,dict):return
    mode=definition.get('verificationMode') or 'outcome'
    require(mode in {'quantitative','outcome'},'请选择量化前后对比或结果 / 定性验证')
    require(not required or text(definition,'expectedSummary'),'请先填写上线后业务效果目标')
    if mode=='outcome':return
    metrics=definition.get('metrics') or []
    require(metrics,'量化验证至少需要一个完整指标');seen=set()
    for i,metric in enumerate(metrics,1):
        for key,label in {'key':'指标编码','label':'指标名称','unit':'单位','baselineValue':'上线前数值','targetValue':'目标数值','measurementWindow':'统计周期','source':'数据来源','direction':'目标方向'}.items():
            require(metric.get(key) is not None and str(metric.get(key)).strip(),f'第 {i} 项指标缺少{label}')
        require(metric['direction'] in {'higher','lower'},f'第 {i} 项指标的目标方向不合法')
        try:valid=all(math.isfinite(float(metric[k])) for k in ['baselineValue','targetValue'])
        except (ValueError,TypeError,OverflowError):valid=False
        require(valid,f'第 {i} 项指标的上线前数值和目标数值必须是有效数字')
        require(metric['key'] not in seen,f"指标编码 {metric['key']} 重复，请合并或修改");seen.add(metric['key'])


def branches(raw,v,require_multiple=False):
    require(isinstance(raw,list),'独立 L3 工作项清单格式不正确')
    active=[x for x in raw if isinstance(x,dict) and text(x,'status')!='removed']
    require(not require_multiple or len(active)>=2,'独立 L3 工作项至少需要 2 个')
    require(len(active)<=30,'一次最多拆分 30 个独立 L3 工作项');result=[];keys=set();titles=set()
    for i,row in enumerate(active,1):
        title=text(row,'title',limit=300);require(title,f'请补充第 {i} 个独立 L3 工作项标题')
        require(title.casefold() not in titles,'独立 L3 工作项标题不能重复');titles.add(title.casefold())
        key=text(row,'branchKey',text(row,'id',f'work-item-{i}'),80)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',key):key=f'work-item-{i}'
        require(key not in keys,'独立 L3 工作项标识不能重复');keys.add(key)
        kind=text(row,'itemKind','feature');relation=text(row,'relationToValue','shared');priority=text(row,'proposedPriority')
        require(kind in {x['key'] for x in v['L3_ITEM_KINDS']},f'第 {i} 个独立 L3 工作项的工作类型不合法')
        require(relation in v['DEMAND_POOL_L3_BRANCH_RELATIONS'],f'第 {i} 个独立 L3 工作项的价值口径不合法')
        require(not priority or priority in {'urgent','planned','normal'},f'第 {i} 个独立 L3 工作项的优先级不合法')
        result.append({'id':text(row,'id'),'branchKey':key,'sortOrder':i,'title':title,'itemKind':kind,
            'scope':text(row,'scope',limit=5000),'difference':text(row,'difference',text(row,'acceptanceDelta'),5000),
            'relationToValue':relation,'proposedPriority':priority,'dependency':text(row,'dependency',limit=5000),
            'formalRequirementId':text(row,'formalRequirementId')})
    return result
