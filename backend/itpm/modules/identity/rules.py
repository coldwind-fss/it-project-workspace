import re
from itpm.core.errors import require

PAGE_KEYS = ['requirements','kanban','knowledge','changelog','sprints','workspace','intake','demandPool','notifications','operations','system']
BASE_ROLES = {
 'super_admin': {'pages': PAGE_KEYS, 'actions': ['*']},
 'admin': {'pages': [x for x in PAGE_KEYS if x != 'system'], 'actions': ['category.manage','project.create','project.update','project.delete','requirement.create','requirement.update','requirement.delete','assignment.manage','recycle.manage','notification.manage','sprint.manage','operation.view','business_request.submit','business_request.manage','demand_pool.manage']},
 'editor': {'pages': ['dashboard','requirements','kanban','knowledge','changelog','sprints','workspace','intake','demandPool'], 'actions': ['project.create','project.update.own','project.delete.own','requirement.create','requirement.update.own','requirement.delete.own','demand.delete.own','sprint.update.own','business_request.submit','demand_pool.manage']},
 'viewer': {'pages': ['dashboard','requirements','kanban','knowledge','changelog','workspace','intake','demandPool'], 'actions': ['business_request.submit']},
}
CUSTOM_ACTIONS = {'project.create','project.update.own','requirement.create','requirement.update.own','sprint.update.own','notification.self','operation.view','demand_pool.manage'}


def name_tokens(value, developers=()):
    text = str(value or '').strip()
    parts = {text, *[x for x in re.split(r'[-－—\s]', text) if x]}
    for d in developers:
        aliases = {d.get('name',''),d.get('shortName',''),d.get('nick',''),*(d.get('aliases') or [])}
        if aliases & parts:
            parts.update(aliases)
    return parts - {''}


def same_name(a, b, developers=()):
    return bool(a and b and name_tokens(a, developers) & name_tokens(b, developers))


def split_people(value):
    return list(dict.fromkeys(x.strip() for x in re.split(r'[,，]', str(value or '')) if x.strip()))

def normalize_person(item,contacts,developers,role=None):
    item=dict(item);name=item.get('name') or item.get('devOwnerName') or '';uid=item.get('userId') or item.get('userid') or item.get('dingUserId') or ''
    match=next((x for x in contacts if uid and uid==(x.get('userId') or x.get('userid') or x.get('dingUserId'))),None)
    if not match:match=next((x for x in contacts if same_name(name,x.get('name') or x.get('devOwnerName'),developers)),None)
    if match:
        item.update(name=match.get('name') or match.get('devOwnerName') or name,userId=match.get('userId') or match.get('userid') or match.get('dingUserId') or uid,
            shortName=match.get('shortName') or match.get('name') or item.get('shortName',''),nick=match.get('nick') or match.get('name') or item.get('nick',''))
    if role:item['role']=role
    return item


def clean_access(data, contacts, developers):
    roles = []
    for r in data.get('customRoles', []):
        key = str(r.get('key') or '').strip()
        if not re.fullmatch(r'custom_[a-z0-9_]{2,40}', key):
            continue
        roles.append({'key':key,'label':str(r.get('label') or key)[:30],'description':str(r.get('description') or '')[:100],
            'pages':[x for x in r.get('pages',[]) if x in PAGE_KEYS],'actions':[x for x in r.get('actions',[]) if x in CUSTOM_ACTIONS]})
    permitted = set(BASE_ROLES) | {r['key'] for r in roles}
    users, seen = [], set()
    for item in data.get('assignments',[]):
        name = str(item.get('name') or item.get('devOwnerName') or '').strip()
        uid = str(item.get('userId') or item.get('userid') or item.get('dingUserId') or '').strip()
        contact = next((c for c in contacts if (uid and uid == (c.get('userid') or c.get('userId'))) or same_name(name,c.get('name'),developers)),{})
        name = contact.get('name') or name
        uid = uid or contact.get('userid') or contact.get('userId') or ''
        marker = uid or name
        if not name or marker in seen: continue
        seen.add(marker)
        users.append({'name':name,'userId':uid,'accessRole':item.get('accessRole') if item.get('accessRole') in permitted else 'viewer',
            'isDeveloper':bool(item.get('isDeveloper')),'enabled':bool(item.get('enabled',True))})
    require(any(x['enabled'] and x['accessRole']=='super_admin' for x in users),'至少保留一名启用中的超级管理员')
    return {'users':users,'customRoles':roles}
