import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { shallowRef } from 'vue'
import type { DTO } from '../../api/compat'
import { getSessionAccess } from '../../api/session-client'
import { ApiError } from '../../api/transport'

export const sessionAccess=shallowRef<DTO<'SessionAccess'>|null>(null)
export const sessionAccessError=shallowRef<ApiError|Error|null>(null)

export async function refreshSessionAccess():Promise<DTO<'SessionAccess'>|null>{
  try{
    const access=await getSessionAccess()
    sessionAccess.value=access
    sessionAccessError.value=null
    const user=JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY)||'{}') as Record<string,unknown>
    localStorage.setItem(SESSION_STORAGE_KEY,JSON.stringify({...user,permissions:access.permissions,actions:access.actions,performanceAllowed:access.performanceAllowed,role:access.role}))
    return access
  }catch(error){sessionAccess.value=null;sessionAccessError.value=error instanceof Error?error:new Error('会话加载失败');return null}
}

const pageKeys:(readonly [string,readonly string[]])[]=[
  ['/system',['system']],['/operations',['operations']],['/notifications',['notifications']],
  ['/demand-pool',['demandPool']],['/intake',['intake']],['/workspace',['workspace']],
  ['/knowledge',['knowledge']],['/sprints',['sprints']],['/changelog',['changelog']],
  ['/requirements/kanban',['kanban']],['/requirements',['requirements']],
  ['/products',['kanban']],['/projects',['kanban']],['/dashboard',['dashboard','kanban']],
  ['/postlaunch/dashboard',['kanban']],['/postlaunch/operations',['workspace']],['/todos',['workspace']],
]
export function canVisitPage(path:string):boolean{
  const access=sessionAccess.value
  if(!access)return false
  if(path==='/performance')return Boolean(access.performanceAllowed)
  if(path==='/system')return access.role==='super_admin'&&access.permissions.includes('system')
  if(path==='/poc-workbench')return access.permissions.includes('demandPool')&&(access.actions.includes('*')||access.actions.includes('demand_pool.manage'))
  const mapping=pageKeys.find(([prefix])=>path===prefix||path.startsWith(prefix+'/'))
  return !mapping||mapping[1].some(key=>access.permissions.includes(key))
}
export function hasAction(action:string):boolean{
  return Boolean(sessionAccess.value?.actions.some(value=>value==='*'||value===action))
}
export function firstAllowedPage():string|null{
  return ['/dashboard','/workspace','/intake','/requirements','/products','/knowledge','/notifications','/operations','/system'].find(canVisitPage)||null
}
