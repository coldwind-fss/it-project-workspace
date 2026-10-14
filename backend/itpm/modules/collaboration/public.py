"""Early phase-change shared fact. Full historical projection/UI in WP03."""
from itpm.infrastructure.database import Repository
from .rules import text

class Collaboration:
    def __init__(self,db,clock,ids):self.repo=Repository(db,['shared_activities']);self.clock,self.ids=clock,ids
    def phase_progress(self,u,p,req,content):
        now=self.clock.now();identifier=self.ids.new('sa',18)
        row={'id':identifier,'scopeType':'requirement','scopeId':req['id'],'projectId':req.get('projectId') or '',
            'requirementId':req['id'],'activityType':'work_progress','title':'阶段更新','content':content,
            'actorUserId':p.userId,'actorName':p.name,'sourceType':'manual','sourceId':identifier,'createdAt':now,'updatedAt':now,'deletedAt':''}
        self.repo.add(u,'shared_activities',row);return row
