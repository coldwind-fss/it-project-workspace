from datetime import datetime,timedelta
from itpm.core.json_fields import object_field


def date(value):
    try:return datetime.strptime(str(value or '')[:10],'%Y-%m-%d').date()
    except ValueError:return None

def in_period(value,period,now):
    today=date(now);starts={'day':today,'week':today-timedelta(days=today.weekday()),'month':today.replace(day=1),
        'quarter':today.replace(month=((today.month-1)//3)*3+1,day=1),'year':today.replace(month=1,day=1)}
    return not starts.get(period) or bool(date(value) and starts[period]<=date(value)<=today)

def entries(value):
    parsed=object_field(value);return parsed.get('metrics') if isinstance(parsed.get('metrics'),list) else []

def result_entries(snapshot,day30):
    result=snapshot.get('metricResults')
    if not isinstance(result,list):result=day30.get('metricResults')
    return result if isinstance(result,list) else []

def number(value):
    try:return float(str(value).strip()) if value is not None and str(value).strip() else None
    except (ValueError,TypeError):return None

def efficiency(card,snapshot):
    if not card:return 0,0
    baseline={str(x['key']):x for x in entries(card.get('baseline')) if isinstance(x,dict) and x.get('key')}
    expected={str(x['key']):x for x in entries(card.get('expected')) if isinstance(x,dict) and x.get('key')};achieved=valid=0
    for result in result_entries(snapshot,object_field(card.get('day30'))):
        if not isinstance(result,dict):continue
        key=str(result.get('key') or '');entry={**baseline.get(key,{}),**expected.get(key,{}),**result};base,target,actual=[number(entry.get(k)) for k in ['baselineValue','targetValue','actualValue']]
        if any(x is None for x in [base,target,actual]):continue
        valid+=1
        if isinstance(entry.get('targetMet'),bool):achieved+=int(entry['targetMet']);continue
        direction=str(entry.get('direction') or '').lower();higher=direction in {'higher','increase','up'} if direction in {'higher','increase','up','lower','decrease','down'} else target>base
        achieved+=int(actual>=target if higher else actual<=target)
    return achieved,valid

def metric_status(card,day7,day30,today):
    base={str(x['key']) for x in entries(card.get('baseline')) if isinstance(x,dict) and x.get('key')};expected={str(x['key']) for x in entries(card.get('expected')) if isinstance(x,dict) and x.get('key')}
    actual={str(x['key']) for x in result_entries(day30.get('responseSnapshot') or {},object_field(card.get('day30'))) if isinstance(x,dict) and x.get('key') and any(x.get(k) is not None and str(x.get(k)).strip() for k in ['actualValue','targetMet'])}
    missing=[label for value,label in [(base,'上线前基线'),(expected,'目标值'),(actual,'上线后实际值')] if not value]
    for row,label in [(day7,'3天回执'),(day30,'30天价值验证')]:
        if row and row.get('scheduledAt') and row['scheduledAt'][:10]<=today and (row.get('sentAt') or row.get('notificationStatus') in {'success','sent'}) and row.get('status')!='submitted':missing.append(label)
    achieved,total=efficiency(card,day30.get('responseSnapshot') or {})
    return {'missing':missing,'hasBaseline':bool(base),'hasExpected':bool(expected),'hasActual':bool(actual),
        'baselineCount':len(base),'expectedCount':len(expected),'actualCount':len(actual),'efficiencyAchieved':achieved,'efficiencyTotal':total}

def lifecycle(item,today):
    day7=item.get('day7Request') or {};day30=item.get('day30Request') or {}
    if day30.get('status')=='submitted':status='待整改' if item.get('openIssueCount') else '已完成'
    elif day30 and (day30.get('sentAt') or day30.get('scheduledAt') and day30['scheduledAt'][:10]<=today):status='价值验证中'
    elif day7 and (day7.get('sentAt') or day7.get('scheduledAt') and day7['scheduledAt'][:10]<=today):status='3天回执待处理' if day7.get('status')!='submitted' else '价值验证中'
    else:status='未开始'
    stage=('30天价值验证' if status!='价值验证中' or day30.get('sentAt') else '3天回执') if status in {'已完成','待整改','价值验证中'} else '3天回执' if status=='3天回执待处理' else '已上线' if item.get('deliveryDate') else '交付记录'
    missing=[label for key,label in [('plannedDeliveryDate','计划交付日期'),('useStartDate','开始使用日期')] if not item.get(key)]
    return {'valueVerificationStatus':status,'lifecycleStage':stage,'lifecycleProgress':{'交付记录':65,'已上线':70,'3天回执':82,'30天价值验证':95}.get(stage,70),
        'dataStatus':'数据不足：缺少'+'、'.join(missing) if missing else status}

def metric(key,label,numerator,denominator,period,coverage,ids,note):
    return {'key':key,'label':label,'value':round(numerator/denominator*100,1) if denominator else None,'numerator':numerator,'denominator':denominator,
        'coverage':round(denominator/coverage*100,1) if coverage else None,'period':period or 'all','operationIds':list(dict.fromkeys(ids)),'note':note}

def unique_requests(requests):
    """Q04: one persisted request ID is one fact; unidentified legacy rows stay separate."""
    result=[];seen=set()
    for request in requests:
        identifier=request.get('id')
        if identifier and identifier in seen:continue
        if identifier:seen.add(identifier)
        result.append(request)
    return result

def pending_count(rows,stage,today):
    pending=[]
    for row in rows:
        if not row.get(stage+'DueDate') or row[stage+'DueDate']>today:continue
        requests=[r for r in row['outcomeRequests'] if r['stage']==stage]
        if any(r['status']=='submitted' for r in requests):continue
        # Preserve the old due-operation count when no request identity exists.
        pending.extend(requests or [{}])
    return len(unique_requests(pending))
