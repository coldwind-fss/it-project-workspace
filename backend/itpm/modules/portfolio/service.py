import json
from itpm.core.json_fields import list_field
from .rules import solution_type,validate_project

PROJECT_FIELDS='name description status solutionType lifecycleTemplate complexityLevel priority department businessOwner devOwner currentVersion startDate targetEndDate categoryId images'.split()

class Portfolio:
    def __init__(self,repo,clock,ids,vocabulary):self.repo,self.clock,self.ids,self.v=repo,clock,ids,vocabulary
    def project(self,u,identifier,lock=False):return self.repo.get(u,'projects',identifier,True,lock)
    def raw_project(self,u,identifier):return self.repo.get(u,'projects',identifier)
    def recycle_rows(self,u,kind):return [x for x in self.repo.find(u,'categories' if kind=='category' else 'projects') if x.get('deletedAt')]
    def recycle_get(self,u,kind,identifier):return self.repo.get(u,'categories' if kind=='category' else 'projects',identifier)
    def recycle_restore(self,u,kind,identifier):self.repo.change(u,'categories' if kind=='category' else 'projects',identifier,dict(deletedAt='',deletedByUserId='',deletedByName=''))
    def recycle_purge(self,u,kind,identifier):self.repo.remove(u,'categories' if kind=='category' else 'projects',identifier)
    def raw_category_children(self,u,identifier):return self.repo.find(u,'projects',{'categoryId':identifier})
    def project_map(self,u):return self.repo.project_map(u)
    def category(self,u,identifier):
        row=self.repo.get(u,'categories',identifier,True)
        if row:row['owner']=list_field(row.get('owner'))
        return row
    def categories(self,u):
        return [{**x,'owner':list_field(x.get('owner'))} for x in self.repo.categories(u)]
    def projects(self,u,category=None,identifier=None):return self.repo.projects(u,category,identifier)
    def category_count(self,u,cid):return self.repo.count_projects(u,cid)
    def create_category(self,u,p,d):
        row={'id':self.ids.new('cat',6),'name':d['name'],'icon':d.get('icon',''),'description':d.get('description',''),'createdAt':self.clock.now()[:10],
            'owner':json.dumps(d.get('owner',[]),ensure_ascii=False),'sortOrder':d.get('sortOrder',0),'color':d.get('color','#3b82f6'),'status':d.get('status','active'),'createdByUserId':p.userId,'createdByName':p.name}
        self.repo.add(u,'categories',row);return self.category(u,row['id'])
    def update_category(self,u,identifier,d):
        values={k:v for k,v in d.items() if k in 'name icon description color status sortOrder'.split()}
        if 'owner' in d:values['owner']=json.dumps(d['owner'],ensure_ascii=False)
        self.repo.change(u,'categories',identifier,values);return self.category(u,identifier)
    def create_project(self,u,p,d):
        validate_project(d,True);st=solution_type(d.get('solutionType'),self.v);now=self.clock.now()
        row={'id':self.ids.new('p',8),'name':d['name'],'description':d.get('description',''),'status':d.get('status','开发中'),'solutionType':st,
            'lifecycleTemplate':d.get('lifecycleTemplate') or st,'complexityLevel':d.get('complexityLevel') or 'medium','priority':d.get('priority','P2'),
            'department':d['department'],'businessOwner':d.get('businessOwner',''),'devOwner':d['devOwner'],'currentVersion':d.get('currentVersion','v1.0.0'),
            'startDate':d.get('startDate',''),'targetEndDate':d['targetEndDate'],'categoryId':d.get('categoryId',''),'images':json.dumps(d.get('images',[]),ensure_ascii=False),
            'createdAt':now,'updatedAt':now,'createdByUserId':p.userId,'createdByName':p.name}
        self.repo.add(u,'projects',row);return self.project(u,row['id'])
    def update_project(self,u,identifier,d):
        values={k:v for k,v in d.items() if k in PROJECT_FIELDS}
        if 'solutionType' in values:values['solutionType']=solution_type(values['solutionType'],self.v)
        if 'lifecycleTemplate' in values:values['lifecycleTemplate']=str(values['lifecycleTemplate'] or '').strip()[:120]
        if isinstance(values.get('images'),list):values['images']=json.dumps(values['images'],ensure_ascii=False)
        if values:values['updatedAt']=self.clock.now()
        self.repo.change(u,'projects',identifier,values);return self.project(u,identifier),bool(values)
    def delete(self,u,p,entity,identifier):
        self.repo.change(u,'categories' if entity=='category' else 'projects',identifier,{'deletedAt':self.clock.now(),'deletedByUserId':p.userId,'deletedByName':p.name})
