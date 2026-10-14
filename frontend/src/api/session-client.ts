import { request } from './transport'
import type { DTO } from './compat'
export async function getSessionAccess():Promise<DTO<'SessionAccess'>>{
  const controller=new AbortController()
  const timeout=window.setTimeout(()=>controller.abort(),8000)
  try{return await request<DTO<'SessionAccess'>>('/session','GET',undefined,undefined,controller.signal)}
  finally{window.clearTimeout(timeout)}
}
