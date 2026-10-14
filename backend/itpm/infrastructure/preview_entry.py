"""Public synthetic entry HTML; authentication is owned by the existing identity module."""
import json

def render_entry(base='/pm-v2/'):
    if not base.startswith('/') or not base.endswith('/') or '..' in base:raise ValueError('Invalid preview base')
    return r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>项目协作空间</title>
<style>body{font:15px/1.8 system-ui;margin:12vh auto;padding:24px;max-width:600px;color:#334155;background:#f8fafc}button{padding:8px 18px;cursor:pointer}small{display:block;color:#64748b}</style>
<h1>项目协作空间</h1><p id="status" role="status">正在进入系统…</p>
<small>当前使用演示数据；钉钉身份与通知使用模拟集成，未向钉钉实际发送消息。</small>
<button id="retry" hidden onclick="location.reload()">重新进入</button><script>
const base=BASE_LITERAL;
(async()=>{
  const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);
  try{
    const params=new URLSearchParams(location.search);
    const requestedActor=params.get('actor')||'super';
    const actor=['super','admin','editor','viewer','other'].includes(requestedActor)?requestedActor:'super';
    const response=await fetch(base+'api/preview/session?actor='+actor,{method:'POST',cache:'no-store',signal:controller.signal});
    if(!response.ok)throw new Error('entry unavailable');
    const result=await response.json();if(!result.user?.sessionToken)throw new Error('invalid session');
    const access=await fetch(base+'api/session',{headers:{'X-PM-Session':result.user.sessionToken},cache:'no-store',signal:controller.signal});
    if(!access.ok)throw new Error('session unavailable');
    localStorage.setItem('itpm-demo-user',JSON.stringify(result.user));
    const requested=params.get('next')||'/dashboard';
    const next=requested.startsWith('/')&&!requested.startsWith('//')&&!/[\r\n#]/.test(requested)?requested:'/dashboard';
    location.replace(base+'#'+next);
  }catch{
    document.getElementById('status').textContent='暂时无法进入系统，请检查网络后重试。如果浏览器禁止网站存储，请允许本站保存会话。';
    document.getElementById('retry').hidden=false;
  }finally{clearTimeout(timer)}
})();</script></html>'''.replace('BASE_LITERAL',json.dumps(base).replace('<','\\u003c'))
