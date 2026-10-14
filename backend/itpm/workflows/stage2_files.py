from itpm.core.errors import require
from itpm.core.ports import Principal
from itpm.modules.identity.public import same_name


def configure_files(access,identity,collaboration,demand,collection,value,value_flow,delivery):
    def demand_owner(u,p,identifier,write=False):return demand.visible(u,p,demand.get(u,identifier))
    def supplement_owner(u,p,identifier,write=False):
        row=demand.source(u,'demand_pool_supplements',identifier);return bool(row and demand.visible(u,p,demand.get(u,row['demandId'])))
    def collection_owner(u,p,identifier,write=False):return bool(collection.response(u,identifier) and demand.manage(u,p))
    def value_owner(u,p,identifier,write=False):
        row=value.request(u,identifier);target=value_flow.target(u,row) if row else None
        if not row:return False
        if row.get('demandId'):return bool(target and demand.visible(u,p,target))
        return p.role in {'admin','super_admin','editor'} or bool(target and (same_name(p.name,target.get('requesterName'),demand.v['DEVELOPERS']) or p.userId and p.userId==target.get('requesterUserId')))
    access.owner_policies.update(demand_pool=demand_owner,demand_pool_supplement=supplement_owner,
        demand_collection_response=collection_owner,demand_pool_value_request=value_owner)
    def token_upload(u,p,kind,identifier,token):
        link=collection.token(u,token);request=value.request(u,token=token) if not link else None
        if request and kind=='demand_pool_value_request':
            require(identifier==request['id'],'无权向该成果确认单上传附件',403,'FORBIDDEN')
            return p if p.authenticated else Principal(userId=request.get('recipientUserId') or '',name=request.get('recipientName') or '钉钉用户')
        if link and kind in {'demand_pool','demand_pool_supplement','demand_collection_response'}:
            did=str(link.get('demandId') or link.get('lastDemandId') or '').strip()
            if kind=='demand_pool_supplement':row=demand.source(u,'demand_pool_supplements',identifier);allowed=bool(row and row['demandId']==did)
            elif kind=='demand_collection_response':row=collection.response(u,identifier);allowed=bool(row and row['recipientToken']==token)
            else:
                row=demand.get(u,identifier);allowed=identifier==did or bool(row and row.get('requesterUserId')==link.get('recipientUserId'))
            require(allowed,'无权向该需求上传附件',403,'FORBIDDEN');return p if p.authenticated else collection.actor(link)
        return None
    def review_download(u,file,token):
        row,source=demand.joined_form(u,'demand_pool_reviews',token=token)
        return bool(row and row['status']!='cancelled' and file and file['ownerType']=='demand_pool' and file['ownerId']==row['demandId'])
    access.token_upload=token_upload;access.review_download=review_download;access.reference_guard=delivery.referenced_file
