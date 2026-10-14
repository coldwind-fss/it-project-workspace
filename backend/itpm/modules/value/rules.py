def policy(demand):
    solution=demand.get('solutionType') or ''
    focused=demand.get('impactScope') in {'cross_department','company'} or demand.get('complexityLevel')=='high' or solution in {'new_app_platform','software_replacement','complex_refactor'}
    level='focused' if focused else 'standard' if solution else 'light'
    guidance={
        'technical_foundation':('技术负责人记录目标指标，业务负责人只需确认影响范围。','目标指标 / 预期改善','当前问题 / 指标（可选）','例如：接口错误率、响应时间、故障次数、恢复时间；暂时没有数字可写“暂无法量化 + 原因”。'),
        'workflow_automation':('业务负责人确认要改善的流程，IT 记录上线前后的证据。','希望流程发生什么变化','现在怎么处理（可选）','例如：现在由几个人、多久处理一次、哪一步最耗时；不知道数字可写大致情况。'),
        'software_replacement':('业务负责人确认替换目标，IT 记录兼容性、使用和迁移结果。','希望替换后达到什么结果','当前软件 / 使用情况（可选）','例如：当前软件、必须保留的功能、使用人数或替换原因。'),
        'new_app_platform':('业务负责人确认首版目标，IT 记录上线和使用证据。','首版要先解决什么','当前做法（可选）','例如：第一版先服务谁、解决哪个场景、预计多少人使用。'),
        'existing_capability':('业务负责人确认结果，IT 记录交付、稳定性和使用证据。','希望具体改变哪一步','当前问题 / 做法（可选）','例如：当前卡点、受影响模块或人员、不能中断的工作。'),
        'data_integration':('业务负责人确认要看到的数据结果，IT 记录准确性和使用情况。','希望看到或打通什么结果','当前数据来源 / 做法（可选）','例如：数据来源、更新频率、当前人工汇总方式和使用人群。')}
    owner,expectation,baseline,hint=guidance.get('existing_capability' if solution=='complex_refactor' else solution,
        ('业务负责人确认目标，IT 记录上线前后的证据。','期望变化','当前情况（可选）','用一句话说明现在怎样、上线后希望怎样即可；没有数字也可以。'))
    return {'level':level,'label':{'light':'轻量记录','standard':'成果假设','focused':'重点验证'}[level],
        'reason':{'focused':'该需求范围较大、复杂度较高或涉及新系统/替换/重构，建议在进入正式交付前先留下可验证的成果假设。',
            'standard':'先记录一句希望带来的变化即可，具体数字可以在上线后根据实际使用情况补充。',
            'light':'尚未完成需求分类，暂不要求填写成果记录；分类后系统会按需提示。'}[level],
        'ownerRole':owner,'expectationLabel':expectation,'baselineLabel':baseline,'metricHint':hint,
        'requiresExpectation':focused,'requiresBaseline':False,'isTechnical':solution=='technical_foundation'}

def metric(value,actual=True,compact=False):
    if not isinstance(value,dict):return {}
    keys=['key','label','unit','source','direction'] if compact else ['key','label','unit','measurementWindow','source','direction']
    result={k:str(value[k] or '').strip()[:120 if compact else 160] for k in keys if value.get(k) is not None and (compact or str(value[k]).strip())}
    for key in ['baselineValue','targetValue']+(['actualValue'] if actual else []):
        raw=value.get(key)
        if raw is not None and not isinstance(raw,(dict,list,bool)) and str(raw).strip():result[key]=raw
    if isinstance(value.get('targetMet'),bool):result['targetMet']=value['targetMet']
    return result

def metrics(value,compact=False):
    if not isinstance(value,list):return []
    rows=[metric(x,compact=compact) for x in value[:50]]
    return [x for x in rows if x.get('key') and any(k in x for k in (['actualValue','targetMet'] if compact else ['baselineValue','targetValue','actualValue','targetMet']))]

def card_metric(value):
    if isinstance(value,str):value={'summary':value}
    if not isinstance(value,dict):return {}
    result={};summary=str(value.get('summary') or '').strip()[:10000]
    if summary:result['summary']=summary
    for key in ['metrics','metricResults']:
        entries=metrics(value.get(key))
        if entries:result[key]=entries
    return result

def receipt(stage,data,card):
    from itpm.core.errors import require
    def text(key,default='',limit=10000):return str(data.get(key) or default).strip()[:limit]
    current=text('currentState');desired=text('desiredChange');summary=text('summary',text('actualResult'));use=text('useStatus',limit=80)
    goal=text('goalStatus',text('targetMet'),80);satisfaction=text('satisfaction',limit=80);effect=text('effectStatus',text('targetMet'),80)
    types=data.get('changeTypes') or []
    if isinstance(types,str):types=types.replace('，',',').split(',')
    changes=[str(x or '').strip()[:80] for x in types if str(x or '').strip()][:8] if isinstance(types,list) else []
    if stage=='day7' and summary:use=use or '已使用';goal=goal or '还无法判断';satisfaction=satisfaction or '基本满意'
    require(stage!='goal' or desired or data.get('noGoal'),'请填写一句希望看到的变化，或选择“暂时没有明确目标”')
    require(stage!='day7' or use and goal and satisfaction,'请完成使用情况、目标结果和整体感受')
    require(stage!='day30' or effect,'请选择实际上线效果')
    require(stage!='day30' or effect not in {'暂无明显改善','暂时无法判断','未达到','否'} or summary,'请补充实际结果或原因')
    issue=text('issueLevel',limit=80)
    if not issue and stage=='day7' and (use in {'已开始使用但有问题','还未开始使用','部分使用'} or goal in {'部分解决','暂未解决'} or satisfaction in {'需要调整','需要改进'}):issue='有问题'
    if not issue and stage=='day30' and effect in {'暂无明显改善','暂时无法判断','未达到','否'}:issue='有问题'
    values={k:dict(card.get(k) or {}) for k in ['baseline','expected','day7','day30']}
    results=[]
    if stage=='goal':
        if current:values['baseline']={'summary':current}
        values['expected']={'summary':desired or '暂时没有明确目标'};status='baseline_ready'
    elif stage=='day7':
        values['day7']={'useStatus':use,'goalStatus':goal,'satisfaction':satisfaction,'summary':summary}
        if issue:values['day7']['issueLevel']=issue
        status='day7_review'
    else:
        results=metrics(data.get('metricResults'),True);values['day30']={'effectStatus':effect,'changeTypes':changes,'summary':summary}
        if results:values['day30']['metricResults']=results
        status='completed'
    snapshot={k:data[k] for k in ['currentState','desiredChange','summary','actualResult','noGoal','useStatus','goalStatus','satisfaction','issueLevel','effectStatus','changeTypes','targetMet'] if k in data}
    if stage=='day30' and results:snapshot['metricResults']=results
    return values,status,text('targetMet',goal or effect or card.get('targetMet') or '',80),snapshot,issue,summary
