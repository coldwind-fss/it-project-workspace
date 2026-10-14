"""Explicit synthetic end-to-end scenario, shared by acceptance and preview seeding."""
import argparse,json,sys
from pathlib import Path

def run_flow(call):
    project=call('POST','/api/projects',{'name':'演示协作产品','department':'隔离测试部','devOwner':'隔离开发者','businessOwner':'隔离业务','solutionType':'custom_application','targetEndDate':'2027-01-01'})
    demand=call('POST','/api/demand-pool',{'title':'演示：减少重复录入与统计','description':'用标准录入和查询替代重复人工整理','department':'隔离测试部','requesterName':'隔离业务','requesterUserId':'stage-viewer','projectId':project['id'],'expectedDeliveryTime':'2027-01-01'},role='viewer')
    did=demand['id'];call('PUT','/api/demand-pool/'+did,{'status':'evaluating','solutionType':'existing_capability'})
    supplement=call('POST','/api/demand-pool/'+did+'/supplements',{'questions':[{'key':'scope','label':'使用范围','required':True}]})
    call('PUT','/api/demand-pool-supplements/'+supplement['id'],{'answers':{'scope':'录入及查询'}},role='viewer')
    call('POST','/api/demand-pool/'+did+'/reviews/reuse',{'contactName':'隔离业务','contactUserId':'stage-viewer','communicationDate':'2026-10-13','decision':'support','prioritySuggestion':'P2','summary':'合成场景：需要录入及查询'})
    call('PUT','/api/demand-pool/'+did+'/decomposition',{'branches':[{'title':'演示录入模块','branchKey':'entry'},{'title':'演示查询模块','branchKey':'query'}],'requireMultiple':True})
    call('PUT','/api/demand-pool/'+did,{'evaluationDecision':'implement','solutionType':'existing_capability'})
    call('PUT','/api/demand-pool/'+did+'/branch-decisions',{'decisions':[{'branchKey':'entry','decision':'implement'},{'branchKey':'query','decision':'implement'}]})
    confirmation=call('POST','/api/demand-pool/'+did+'/confirmations',{'content':{'scope':'录入及查询','scenarios':'业务日常录入','expected':'录入后可查询','valueDefinition':{'verificationMode':'outcome','expectedSummary':'减少重复劳动'}}})
    call('POST','/api/demand-pool-confirmations/by-token',{'token':confirmation['token'],'decision':'confirmed'},role='viewer')
    converted=call('POST','/api/demand-pool/'+did+'/convert',{'projectId':project['id'],'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'})
    assert len(converted['requirementIds'])==2
    repeated=call('POST','/api/demand-pool/'+did+'/convert',{'projectId':project['id'],'assignee':'隔离开发者','expectedDeliveryTime':'2027-01-01'})
    assert repeated['requirementIds']==converted['requirementIds']
    rounds=[];links=[]
    for index,rid in enumerate(converted['requirementIds']):
        baseline=call('GET','/api/requirements/'+rid+'/delivery-baselines')['items'][0]
        link=call('POST','/api/requirements/'+rid+'/collaboration-links',{'clientKey':'k4-verification-'+str(index),'kind':'verification','title':'演示：请验证交付','content':'核对录入和查询','recipientName':'隔离业务','baselineId':baseline['id']})
        headers={'X-PM-Collaboration-Token':link['link'].split('token=')[1]}
        call('GET','/api/collaboration-link/context',headers=headers)
        call('POST','/api/collaboration-link/submit',{'outcome':'passed','content':'合成验收通过'},headers=headers)
        assert call('GET','/api/requirements/'+rid)['status']=='待交付'
        op=call('POST','/api/requirements/'+rid+'/deliveries',{'clientKey':'k4-delivery-'+str(index),'acceptanceRequestId':link['id'],'deliveryDate':'2026-09-01','useStartDate':'2026-09-01'})
        assert len(op['outcomeRequests'])==2 and op['day7DueDate']=='2026-09-04' and op['day30DueDate']=='2026-10-01'
        for request in op['outcomeRequests']:
            sent=call('POST','/api/demand-pool-value-requests/'+request['id']+'/send')
            receipt={'token':sent['token'],'summary':'合成回执：录入查询已使用'}
            if request['stage']=='day7':receipt.update(useStatus='已正常使用',satisfaction='满意',goalStatus='已解决')
            else:receipt.update(effectStatus='有明显改善')
            call('POST','/api/demand-pool-outcome-submit',receipt,role='viewer')
            call('POST','/api/demand-pool-value-requests/'+request['id']+'/view')
        rounds.append(op['id']);links.append(link['link'])
    poc=call('POST','/api/poc-workbench/records',{'title':'演示：录入方案验证','projectId':project['id'],'requirementId':converted['requirementIds'][0],'objective':'验证录入可查询','status':'completed','conclusion':'passed','result':'合成验证通过'})
    ai=call('POST','/api/poc-workbench/records/'+poc['id']+'/derive-capability',{})
    call('POST','/api/postlaunch/knowledge',{'operationId':rounds[0],'title':'演示：标准录入方法','content':'录入后检查查询结果','status':'published'})
    call('POST','/api/postlaunch/proposals',{'operationId':rounds[0],'title':'演示：优化输入提示','suggestion':'增加字段说明'})
    target=call('POST','/api/notification/targets',{'name':'演示：个人工作报告','deliveryChannel':'personal','recipientUserId':'stage-viewer','scope':'dashboard'})
    call('POST','/api/notification/preview',{'targetId':target['id'],'scope':'dashboard'})
    sent=call('POST','/api/notification/sync',{'targetId':target['id']});assert sent['ok']==1
    sync=call('POST','/api/work-intake',{'projectId':project['id'],'mode':'commit','idempotencyKey':'k4-demo-sync','notify':False,'records':[{'title':'演示：技术规范整理','developerOwner':'隔离开发者','businessOwner':'隔离业务','status':'in_progress','logs':[{'content':'合成工作记录：接口契约、事务和模块边界已接入'}]}]})
    dashboard=call('GET','/api/postlaunch/dashboard?keyword=演示')
    assert len(dashboard['rows'])==2
    metrics={r['key']:r for r in dashboard['metrics']};assert metrics['responseRate']['denominator']==4
    assert metrics['satisfactionRate']['denominator']==2 and metrics['efficiencyRate']['denominator']==0
    call('GET','/api/work-reports?period=month');call('GET','/api/dashboard/stats')
    return {'projectId':project['id'],'demandId':did,'requirementIds':converted['requirementIds'],'operationIds':rounds,'pocId':poc['id'],'aiId':ai['id'],
        'notificationId':target['id'],'syncBatchId':sync['batchId'],'collaborationLinks':links,'confirmationToken':confirmation['token'],'metrics':metrics}

def main():
    import httpx
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    if not args.url.startswith('http://127.0.0.1:'):raise SystemExit('Explicit loopback synthetic preview required')
    with httpx.Client(base_url=args.url,timeout=30) as client:
        existing=client.get('/api/projects',headers={'X-PM-Session':'fixture-stage-super'});existing.raise_for_status()
        if any(x['name']=='演示协作产品' for x in existing.json()):raise SystemExit('Demo already exists; refuse to add duplicates')
        def call(method,path,payload=None,role='super',headers=None):
            r=client.request(method,path,json=payload,headers={'X-PM-Session':'fixture-stage-'+role,**(headers or {})});r.raise_for_status();return r.json()
        result=run_flow(call)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Synthetic full product flow populated; identities/tokens stored privately, not printed')
if __name__=='__main__':main()
