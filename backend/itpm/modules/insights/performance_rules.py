"""V1 scoring formulas over explicit evidence; no database or clock IO."""

from itpm.core.json_fields import object_field

from itpm.modules.postlaunch.public import date,number,entries,result_entries

def _performance_number(value): return number(value)

_postlaunch_date=date

_postlaunch_metric_entries=entries

_postlaunch_response_metric_entries=result_entries

parse_json_object_field=object_field

PERFORMANCE_RULE_VERSION = 'performance-v2-2026-09'

PERFORMANCE_ALLOWED_NAMES = ('十叶', '十叶-冯硕硕', '冯硕硕')

PERFORMANCE_RULES = [{'index': 1, 'key': 'delivery', 'indicator': '业务需求管理与项目交付', 'weight': 0.15, 'text': '需求管理3分：按标准《业务需求问卷》收集当前问题、使用对象、现有方式、预期结果、优先级、上线时间及验收人；收到需求后1个工作日内响应，信息不清晰造成返工扣分。按期交付6分：项目负责人、里程碑、预计上线时间及风险明确；按期交付率≥95%得6分，90%—94%得5分，80%—89%得4分，70%—79%得2分，＜70%得0分。验收质量4分：上线前完成业务验收，一次验收通过率≥90%得4分，80%—89%得3分，70%—79%得2分，＜70%得0—1分。过程管理2分：记录进度、风险及待确认事项，预计延期原则上至少提前2个工作日反馈。', 'sources': [('requirements', '需求台账'), ('demand_pool', '需求池'), ('acceptance', '验收记录'), ('postlaunch_operations', '上线记录'), ('work_logs', '过程操作记录')]}, {'index': 2, 'key': 'value', 'indicator': '业务提效与实际价值', 'weight': 0.2, 'text': '价值验证8分：重点项目开发前至少记录1项业务基线，如耗时、步骤、人工投入、错误率、处理量或成本；上线后7—30天进行前后对比，无基线或无结果验证的项目不得按完整价值交付认定。提效结果6分：核心项目效率、成本、错误率或人工投入等综合改善≥30%得6分，20%—29%得5分，10%—19%得3分，＜10%得0—2分。实际使用4分：上线30天目标用户使用率≥70%得4分，50%—69%得3分，30%—49%得2分，＜30%得0—1分。低价值控制2分：识别重复建设、低价值或低投入产出比需求，并提出简化、合并、暂缓或替代方案。', 'sources': [('value_card', '业务基线与价值卡'), ('postlaunch_value', '30天价值验证'), ('usage', '使用状态回执'), ('proposals', 'IT决策/改善提案')]}, {'index': 3, 'key': 'satisfaction', 'indicator': '业务满意度与使用效果', 'weight': 0.15, 'text': '满意度8分：重点项目上线后由实际使用人员填写标准满意度问卷，平均≥4.6/5得8分，4.3—4.59得7分，4.0—4.29得5分，3.5—3.99得3分，＜3.5得0—2分。回访优化4分：重点项目上线7—14天内完成回访，对使用障碍和低分反馈形成改进动作。问题闭环3分：低分项目及重大使用问题有明确负责人和处理结果，重复投诉或长期未处理按影响扣分。', 'sources': [('day7_feedback', '3天回执'), ('satisfaction', '满意度问卷'), ('issues', '问题台账'), ('postlaunch_operations', '回访记录')]}, {'index': 4, 'key': 'ai', 'indicator': 'AI探索、验证与创新落地', 'weight': 0.2, 'text': 'AI主动探索5分：每月至少完成2项有效探索，必须说明真实业务场景、与现有方案差异、成本/接入难度及公司应用价值，纯资讯或简单Demo不计入。PoC验证5分：每月至少完成1项围绕真实业务问题的PoC，并对质量、准确率、效率、成本、稳定性或人工干预中的至少2项进行测试。AI业务落地5分：原则上每季度至少推动1项AI能力进入真实业务试运行或正式使用，停留在Demo不视为落地。Benchmark与迭代5分：重要AI项目须与人工方案、现有AI方案及新方案进行必要比较并形成结论。', 'sources': [('ai_exploration', 'AI探索/需求记录'), ('poc', 'PoC记录'), ('benchmark', 'Benchmark记录'), ('postlaunch_operations', '上线与使用记录')]}, {'index': 5, 'key': 'stability', 'indicator': '系统稳定性与持续优化', 'weight': 0.1, 'text': '系统稳定性3分：负责系统、接口及自动化流程稳定运行，因可避免的代码、配置、权限或发布问题造成重大业务中断按影响扣分。问题响应3分：核心业务紧急问题原则上30分钟内响应，一般问题4小时内响应；无法立即解决时须反馈原因、临时方案及预计完成时间。重复问题控制2分：重大故障形成原因及预防措施，同原因重大问题重复发生从严扣分。持续优化2分：每月至少进行1次系统健康检查，并持续处理历史遗留问题。', 'sources': [('system_logs', '系统日志'), ('issues', '故障/问题台账'), ('response', '响应时间记录'), ('health_check', '健康检查记录')]}, {'index': 6, 'key': 'improvement', 'indicator': '主动性、跨部门协同与知识沉淀', 'weight': 0.1, 'text': '主动改善3分：每月至少主动提出2项流程、系统、自动化或AI改善建议，不得全部来源于业务部门被动提需求。跨部门协同3分：重点项目主动完成需求确认、方案沟通、测试及验收；对明显不合理或低价值需求提出专业判断及替代方案。文档沉淀2分：重点系统具备使用、权限、异常处理及维护文档，避免核心事项仅由个人掌握。知识分享2分：每月至少完成1次AI新能力、项目案例、PoC结果或经验复盘分享。', 'sources': [('proposals', '改善提案'), ('requirements', '项目/协作记录'), ('knowledge', '知识库'), ('share', '分享记录')]}, {'index': 7, 'key': 'discipline', 'indicator': '工作纪律与职业态度', 'weight': 0.1, 'text': '效率50%：每日及时输出日报，并与直属领导/项目组成员确认工作进度；未按要求执行每次扣2分，提前/按时完成得4—5分，延期1天得1—3分，拖延2天及以上得0分。态度50%：能够高效协同、主动推进得4—5分，被动需督促得1—3分，态度欠佳或同类错误重复发生得0分。保密、考勤和直属领导主观评价在系统未接入前不自动计分。', 'sources': [('work_logs', '工作日志/计划记录'), ('todos', '待办记录'), ('leader_review', '直属领导评价'), ('compliance', '考勤与合规数据')]}]

def _performance_source(source_type, label, rows, month, note=''):
    rows = rows or []
    return {'type': source_type, 'label': label, 'count': len(rows), 'period': month, 'recordIds': [str(x.get('id') or '') for x in rows if x.get('id')], 'note': note}

def _performance_fact(label, value=None, numerator=None, denominator=None, note=''):
    item = {'label': label, 'value': value if value is not None else '暂无数据'}
    if numerator is not None:
        item['numerator'] = numerator
    if denominator is not None:
        item['denominator'] = denominator
    if note:
        item['note'] = note
    return item

def _performance_rate(numerator, denominator):
    return round(numerator / denominator * 100, 1) if denominator else None

def _performance_band(value, bands):
    if value is None:
        return (None, '暂无数据')
    for minimum, score, label in bands:
        if value >= minimum:
            return (score, label)
    return (bands[-1][1], bands[-1][2])

def _performance_metric_facts(operations):
    facts, complete = ([], [])
    for operation in operations:
        card = operation.get('valueCard') or {}
        baseline = {str(x.get('key') or ''): x for x in _postlaunch_metric_entries(card.get('baseline')) if isinstance(x, dict) and x.get('key')}
        expected = {str(x.get('key') or ''): x for x in _postlaunch_metric_entries(card.get('expected')) if isinstance(x, dict) and x.get('key')}
        day30 = parse_json_object_field(card.get('day30'))
        snapshot = (operation.get('day30Request') or {}).get('responseSnapshot') or {}
        result_rows = _postlaunch_response_metric_entries(snapshot, day30)
        actual = {str(x.get('key') or ''): x for x in result_rows if isinstance(x, dict) and x.get('key')}
        for key, metric in baseline.items():
            result = actual.get(key) or {}
            before = _performance_number(metric.get('baselineValue'))
            target = _performance_number((expected.get(key) or metric).get('targetValue'))
            after = _performance_number(result.get('actualValue'))
            target_met = result.get('targetMet') if isinstance(result.get('targetMet'), bool) else None
            if target_met is None and after is not None and (target is not None):
                direction = metric.get('direction') or (expected.get(key) or {}).get('direction')
                target_met = after >= target if direction == 'higher' else after <= target if direction == 'lower' else None
            improvement = None
            direction = metric.get('direction') or (expected.get(key) or {}).get('direction')
            if before not in (None, 0) and after is not None and (direction in {'higher', 'lower'}):
                improvement = round((after - before if direction == 'higher' else before - after) / abs(before) * 100, 1)
            item = {'operationId': operation.get('id'), 'title': operation.get('title') or operation.get('projectName') or operation.get('id'), 'key': key, 'label': metric.get('label') or key, 'unit': metric.get('unit') or '', 'baselineValue': metric.get('baselineValue'), 'targetValue': (expected.get(key) or metric).get('targetValue'), 'actualValue': result.get('actualValue'), 'direction': direction or '', 'targetMet': target_met, 'improvementPercent': improvement, 'measurementWindow': metric.get('measurementWindow') or '', 'source': metric.get('source') or ''}
            facts.append(item)
            if before is not None and target is not None and (after is not None):
                complete.append(item)
    return (facts, complete)

def score_evidence(operations, requirements, issues, proposals, knowledge, pocs, work_logs, month, user_name, generated_at):
    value_operations = [row for row in operations if row.get('valueVerificationEligible')]
    on_time_rows = [row for row in operations if _postlaunch_date(row.get('plannedDeliveryDate')) and _postlaunch_date(row.get('actualDeliveryDate'))]
    on_time_count = sum((1 for row in on_time_rows if _postlaunch_date(row.get('actualDeliveryDate')) <= _postlaunch_date(row.get('plannedDeliveryDate'))))
    acceptance_rows = [row for row in operations if row.get('acceptanceOutcome')]
    acceptance_pass = sum((1 for row in acceptance_rows if row.get('acceptanceOutcome') == 'passed'))
    day7_rows = [row for row in value_operations if (row.get('day7Request') or {}).get('status') == 'submitted' and isinstance((row.get('day7Request') or {}).get('responseSnapshot'), dict)]
    valid_satisfaction_rows = [row for row in day7_rows if (row.get('day7Request') or {}).get('responseSnapshot', {}).get('satisfaction')]
    satisfied_rows = [row for row in valid_satisfaction_rows if (row.get('day7Request') or {}).get('responseSnapshot', {}).get('satisfaction') in {'满意', '基本满意'}]
    usable_rows = [row for row in day7_rows if (row.get('day7Request') or {}).get('responseSnapshot', {}).get('useStatus') in {'已正常使用', '正常使用', '已开始使用但有问题'}]
    metric_facts, complete_metrics = _performance_metric_facts(value_operations)
    target_met_metrics = [row for row in complete_metrics if row.get('targetMet') is True]
    improvement_values = [row.get('improvementPercent') for row in complete_metrics if row.get('improvementPercent') is not None]
    avg_improvement = round(sum(improvement_values) / len(improvement_values), 1) if improvement_values else None
    requirements_complete = [row for row in requirements if all((str(row.get(field) or '').strip() for field in ('title', 'description', 'requester', 'assignee', 'expectedDeliveryTime', 'acceptanceCriteria')))]
    delivery_gaps = []
    if not requirements:
        delivery_gaps.append('暂无当月需求台账记录')
    elif len(requirements_complete) < len(requirements):
        delivery_gaps.append(f'{len(requirements) - len(requirements_complete)} 条需求缺少结构化确认字段')
    if not on_time_rows:
        delivery_gaps.append('缺少可比较的计划交付日期与实际交付日期')
    if not acceptance_rows:
        delivery_gaps.append('暂无已提交的业务验收轮次')
    delivery_facts = [_performance_fact('结构化需求完整率', f'{_performance_rate(len(requirements_complete), len(requirements))}%' if requirements else None, len(requirements_complete), len(requirements)), _performance_fact('按期交付率', f'{_performance_rate(on_time_count, len(on_time_rows))}%' if on_time_rows else None, on_time_count, len(on_time_rows)), _performance_fact('首轮验收通过率', f'{_performance_rate(acceptance_pass, len(acceptance_rows))}%' if acceptance_rows else None, acceptance_pass, len(acceptance_rows)), _performance_fact('过程操作记录', f'{len(work_logs)} 条', len(work_logs), note='来自工作日志/操作记录')]
    on_time_score, on_time_basis = _performance_band(_performance_rate(on_time_count, len(on_time_rows)), [(95, 6, '≥95%档'), (90, 5, '90%—94%档'), (80, 4, '80%—89%档'), (70, 2, '70%—79%档'), (0, 0, '＜70%档')])
    acceptance_score, acceptance_basis = _performance_band(_performance_rate(acceptance_pass, len(acceptance_rows)), [(90, 4, '≥90%档'), (80, 3, '80%—89%档'), (70, 2, '70%—79%档'), (0, 0, '＜70%档')])
    delivery_row = {'index': 1, 'key': 'delivery', 'indicator': '业务需求管理与项目交付', 'scoringRule': {'text': PERFORMANCE_RULES[0]['text'], 'subItems': [{'key': 'requirement_management', 'label': '需求管理', 'maxScore': 3}, {'key': 'on_time', 'label': '按期交付', 'maxScore': 6}, {'key': 'acceptance', 'label': '验收质量', 'maxScore': 4}, {'key': 'process', 'label': '过程管理', 'maxScore': 2}]}, 'dataSources': [_performance_source(kind, label, {'requirements': requirements, 'demand_pool': requirements, 'acceptance': acceptance_rows, 'postlaunch_operations': operations, 'work_logs': work_logs}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[0]['sources']], 'completion': {'status': 'partial' if delivery_gaps else 'calculated', 'summary': f'本月归集 {len(requirements)} 条需求、{len(operations)} 条上线记录；' + (f'按期交付 {on_time_count}/{len(on_time_rows)}。' if on_time_rows else '按期交付待补计划日期和实际日期。'), 'facts': delivery_facts, 'gaps': delivery_gaps, 'evidenceIds': [str(x.get('id')) for x in operations + requirements if x.get('id')]}, 'score': {'value': None, 'max': 15, 'autoValue': sum((x for x in (on_time_score, acceptance_score) if x is not None)), 'autoMax': 10 if on_time_score is not None and acceptance_score is not None else 0, 'basis': '；'.join((x for x in [f'按期交付{on_time_basis}' if on_time_score is not None else '', f'验收{acceptance_basis}' if acceptance_score is not None else '', '需求响应/过程管理待补结构化时长或人工评价'] if x))}, 'weight': 0.15}
    value_gaps = []
    if not value_operations:
        value_gaps.append('暂无可关联的上线项目')
    if not metric_facts:
        value_gaps.append('缺少上线前基线、目标值或30天实际值')
    if any((not row.get('direction') for row in metric_facts)):
        value_gaps.append('部分历史指标缺少目标方向，无法精确计算改善比例')
    value_facts = [_performance_fact('结构化指标完整数', f'{len(complete_metrics)}/{len(metric_facts)}' if metric_facts else None, len(complete_metrics), len(metric_facts)), _performance_fact('达成目标指标', f'{len(target_met_metrics)}/{len(complete_metrics)}' if complete_metrics else None, len(target_met_metrics), len(complete_metrics)), _performance_fact('平均改善比例', f'{avg_improvement}%' if avg_improvement is not None else None, note='仅统计同时具备基线、目标、实际值和目标方向的指标')]
    value_row = {'index': 2, 'key': 'value', 'indicator': '业务提效与实际价值', 'scoringRule': {'text': PERFORMANCE_RULES[1]['text'], 'subItems': [{'key': 'value_verification', 'label': '价值验证', 'maxScore': 8}, {'key': 'improvement', 'label': '提效结果', 'maxScore': 6}, {'key': 'usage', 'label': '实际使用', 'maxScore': 4}, {'key': 'low_value_control', 'label': '低价值控制', 'maxScore': 2}]}, 'dataSources': [_performance_source(kind, label, {'value_card': value_operations, 'postlaunch_value': value_operations, 'usage': day7_rows, 'proposals': proposals}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[1]['sources']], 'completion': {'status': 'partial' if value_gaps else 'calculated', 'summary': f'已归集 {len(metric_facts)} 项结构化指标，完整可比 {len(complete_metrics)} 项；' + (f'达成目标 {len(target_met_metrics)} 项。' if complete_metrics else '当前尚不能形成前后对比结论。'), 'facts': value_facts, 'gaps': value_gaps, 'evidenceIds': list(dict.fromkeys([str(x.get('operationId')) for x in metric_facts if x.get('operationId')] + [str(x.get('id')) for x in proposals if x.get('id')]))}, 'score': {'value': None, 'max': 20, 'autoValue': None, 'autoMax': 0, 'basis': '价值验证、改善幅度和30天用户使用率需同时具备对应数据后结算'}, 'weight': 0.2}
    satisfaction_gaps = []
    if not valid_satisfaction_rows:
        satisfaction_gaps.append('暂无有效3天回执')
    if valid_satisfaction_rows and (not any((str((row.get('day7Request') or {}).get('responseSnapshot', {}).get('satisfactionScore') or '').strip() for row in valid_satisfaction_rows))):
        satisfaction_gaps.append('当前回访为三档满意度，尚未接入绩效表要求的五级评分')
    satisfaction_row = {'index': 3, 'key': 'satisfaction', 'indicator': '业务满意度与使用效果', 'scoringRule': {'text': PERFORMANCE_RULES[2]['text'], 'subItems': [{'key': 'satisfaction', 'label': '满意度', 'maxScore': 8}, {'key': 'callback', 'label': '回访优化', 'maxScore': 4}, {'key': 'issue_closure', 'label': '问题闭环', 'maxScore': 3}]}, 'dataSources': [_performance_source(kind, label, {'day7_feedback': day7_rows, 'satisfaction': valid_satisfaction_rows, 'issues': issues, 'postlaunch_operations': value_operations}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[2]['sources']], 'completion': {'status': 'partial' if satisfaction_gaps else 'calculated', 'summary': f'有效3天回执 {len(valid_satisfaction_rows)} 条，满意/基本满意 {len(satisfied_rows)} 条；已使用状态 {len(usable_rows)} 条。', 'facts': [_performance_fact('有效3天回执', f'{len(valid_satisfaction_rows)} 条'), _performance_fact('满意/基本满意', f'{len(satisfied_rows)}/{len(valid_satisfaction_rows)}' if valid_satisfaction_rows else None, len(satisfied_rows), len(valid_satisfaction_rows)), _performance_fact('已开始使用', f'{len(usable_rows)}/{len(day7_rows)}' if day7_rows else None, len(usable_rows), len(day7_rows))], 'gaps': satisfaction_gaps, 'evidenceIds': [str(x.get('id')) for x in operations if x.get('id')]}, 'score': {'value': None, 'max': 15, 'autoValue': None, 'autoMax': 0, 'basis': '需补五级满意度分值、回访时效和问题闭环结果后结算'}, 'weight': 0.15}
    ai_gaps = []
    if len(pocs) < 1:
        ai_gaps.append('暂无PoC记录；AI探索和Benchmark尚未形成独立结构化来源')
    ai_row = {'index': 4, 'key': 'ai', 'indicator': 'AI探索、验证与创新落地', 'scoringRule': {'text': PERFORMANCE_RULES[3]['text'], 'subItems': [{'key': 'exploration', 'label': 'AI主动探索', 'maxScore': 5}, {'key': 'poc', 'label': 'PoC验证', 'maxScore': 5}, {'key': 'landing', 'label': 'AI业务落地', 'maxScore': 5}, {'key': 'benchmark', 'label': 'Benchmark与迭代', 'maxScore': 5}]}, 'dataSources': [_performance_source(kind, label, {'ai_exploration': requirements, 'poc': pocs, 'benchmark': [], 'postlaunch_operations': value_operations}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[3]['sources']], 'completion': {'status': 'partial' if ai_gaps else 'calculated', 'summary': f'本月归集 {len(pocs)} 条PoC记录；探索、落地和Benchmark需补专门记录才能按原评分细则结算。', 'facts': [_performance_fact('PoC记录', f'{len(pocs)} 条', len(pocs)), _performance_fact('本月探索目标', '≥2 项'), _performance_fact('本月PoC目标', '≥1 项')], 'gaps': ai_gaps, 'evidenceIds': [str(x.get('id')) for x in pocs if x.get('id')]}, 'score': {'value': None, 'max': 20, 'autoValue': None, 'autoMax': 0, 'basis': '当前仅接入PoC记录，不能用记录条数替代探索有效性、落地和Benchmark得分'}, 'weight': 0.2}
    stability_gaps = ['系统日志、故障响应时长、健康检查和重复问题字段尚未统一接入']
    stability_row = {'index': 5, 'key': 'stability', 'indicator': '系统稳定性与持续优化', 'scoringRule': {'text': PERFORMANCE_RULES[4]['text'], 'subItems': [{'key': 'stability', 'label': '系统稳定性', 'maxScore': 3}, {'key': 'response', 'label': '问题响应', 'maxScore': 3}, {'key': 'repeat_control', 'label': '重复问题控制', 'maxScore': 2}, {'key': 'health_check', 'label': '持续优化', 'maxScore': 2}]}, 'dataSources': [_performance_source(kind, label, {'system_logs': [], 'issues': issues, 'response': issues, 'health_check': []}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[4]['sources']], 'completion': {'status': 'partial', 'summary': f"归集问题/故障记录 {len(issues)} 条，其中已关闭 {sum((1 for x in issues if x.get('status') == '已关闭'))} 条；响应及时率和健康检查待补。", 'facts': [_performance_fact('问题记录', f'{len(issues)} 条'), _performance_fact('已关闭问题', f"{sum((1 for x in issues if x.get('status') == '已关闭'))}/{len(issues)}" if issues else None)], 'gaps': stability_gaps, 'evidenceIds': [str(x.get('id')) for x in issues if x.get('id')]}, 'score': {'value': None, 'max': 10, 'autoValue': None, 'autoMax': 0, 'basis': '问题记录可追溯，但当前不能从状态条数推断稳定性得分'}, 'weight': 0.1}
    improvement_gaps = []
    if len(proposals) < 2:
        improvement_gaps.append('主动改善提案未达到每月2项或暂无记录')
    if not knowledge:
        improvement_gaps.append('暂无知识沉淀记录；文档覆盖和分享记录尚未接入')
    improvement_row = {'index': 6, 'key': 'improvement', 'indicator': '主动性、跨部门协同与知识沉淀', 'scoringRule': {'text': PERFORMANCE_RULES[5]['text'], 'subItems': [{'key': 'proactive', 'label': '主动改善', 'maxScore': 3}, {'key': 'collaboration', 'label': '跨部门协同', 'maxScore': 3}, {'key': 'documentation', 'label': '文档沉淀', 'maxScore': 2}, {'key': 'sharing', 'label': '知识分享', 'maxScore': 2}]}, 'dataSources': [_performance_source(kind, label, {'proposals': proposals, 'requirements': requirements, 'knowledge': knowledge, 'share': []}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[5]['sources']], 'completion': {'status': 'partial' if improvement_gaps else 'calculated', 'summary': f'归集改善提案 {len(proposals)} 条、知识记录 {len(knowledge)} 条；协同和分享仍需对应记录。', 'facts': [_performance_fact('改善提案', f'{len(proposals)} 条', len(proposals)), _performance_fact('知识记录', f'{len(knowledge)} 条', len(knowledge))], 'gaps': improvement_gaps, 'evidenceIds': [str(x.get('id')) for x in proposals + knowledge if x.get('id')]}, 'score': {'value': None, 'max': 10, 'autoValue': None, 'autoMax': 0, 'basis': '提案和知识记录可展示，但不能替代协同质量、文档覆盖和分享频次评价'}, 'weight': 0.1}
    discipline_row = {'index': 7, 'key': 'discipline', 'indicator': '工作纪律与职业态度', 'scoringRule': {'text': PERFORMANCE_RULES[6]['text'], 'subItems': [{'key': 'efficiency', 'label': '效率', 'maxScore': 5}, {'key': 'attitude', 'label': '态度', 'maxScore': 5}]}, 'dataSources': [_performance_source(kind, label, {'work_logs': work_logs, 'todos': [], 'leader_review': [], 'compliance': []}.get(kind, []), month) for kind, label in PERFORMANCE_RULES[6]['sources']], 'completion': {'status': 'pending_manual', 'summary': f'系统归集工作日志 {len(work_logs)} 条；直属领导评价、考勤与合规数据未接入，不自动计分。', 'facts': [_performance_fact('工作日志', f'{len(work_logs)} 条', len(work_logs))], 'gaps': ['待直属领导填写效率与态度评分', '考勤/合规数据未接入'], 'evidenceIds': [str(x.get('id')) for x in work_logs if x.get('id')]}, 'score': {'value': None, 'max': 10, 'autoValue': None, 'autoMax': 0, 'basis': '待直属领导人工评分；系统只提供工作事实证据'}, 'weight': 0.1}
    rows = [delivery_row, value_row, satisfaction_row, ai_row, stability_row, improvement_row, discipline_row]
    auto_value = sum((float(row['score'].get('autoValue') or 0) for row in rows))
    auto_max = sum((float(row['score'].get('autoMax') or 0) for row in rows))
    complete_count = sum((1 for row in rows if row['completion'].get('status') == 'calculated'))
    evidence = {'delivery': [{'id': x.get('id'), 'title': x.get('title') or x.get('projectName'), 'date': x.get('deliveryDate'), 'kind': x.get('deliveryKind')} for x in operations], 'value': [{'id': x.get('id'), 'title': x.get('title') or x.get('projectName'), 'date': x.get('useStartDate')} for x in value_operations if x.get('day30RequestId')], 'satisfaction': [{'id': x.get('id'), 'title': x.get('title') or x.get('projectName')} for x in value_operations], 'ai': [{'id': x.get('id'), 'title': x.get('title') or 'PoC 记录', 'date': x.get('createdAt'), 'conclusion': x.get('conclusion') or x.get('status')} for x in pocs], 'stability': [{'id': x.get('id'), 'title': x.get('title'), 'status': x.get('status'), 'severity': x.get('severity')} for x in issues], 'improvement': [{'id': x.get('id'), 'title': x.get('title'), 'status': x.get('status')} for x in proposals], 'discipline': [{'id': x.get('id'), 'title': x.get('title') or x.get('logType'), 'date': x.get('occurredAt') or x.get('createdAt')} for x in work_logs]}
    return {'month': month, 'userName': user_name, 'ruleVersion': PERFORMANCE_RULE_VERSION, 'generatedAt': generated_at, 'counts': {'operations': len(operations), 'requirements': len(requirements), 'issues': len(issues), 'proposals': len(proposals), 'knowledge': len(knowledge), 'pocs': len(pocs), 'workLogs': len(work_logs)}, 'summary': {'totalScore': None, 'autoScore': auto_value, 'autoScoreMax': auto_max, 'pendingScore': round(70 - auto_value, 1), 'dataCompleteness': round(complete_count / len(rows) * 100, 1), 'pendingCount': sum((1 for row in rows if row['completion'].get('status') != 'calculated'))}, 'rows': rows, 'evidence': evidence}
