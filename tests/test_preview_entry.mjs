// Exercise the actual redirect helper and served entry script without a real provider.
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'

const root=fileURLToPath(new URL('..',import.meta.url))
const require=createRequire(path.join(root,'frontend/package.json'))
const ts=require('typescript')
const source=fs.readFileSync(path.join(root,'frontend/src/features/access/preview-entry.ts'),'utf8')
const code=ts.transpileModule(source.replace('import.meta.env.VITE_PREVIEW_ENTRY',"'/pm-v2/preview-login'"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText
const data=new Map();let locationTarget='';let now=100000;let reloads=0
const exports={}
vm.runInNewContext(code,{exports,require:()=>({shallowRef:value=>({value})}),URL,Date:{now:()=>now},sessionStorage:{getItem:key=>data.get(key)||null,setItem:(key,value)=>data.set(key,value),removeItem:key=>data.delete(key)},window:{location:{origin:'http://127.0.0.1:18884',replace:url=>locationTarget=url,reload:()=>reloads++}}})
assert.equal(exports.enterPreview('/operations?origin=resume'),true)
assert.equal(new URL(locationTarget).searchParams.get('next'),'/operations?origin=resume')
assert.equal(exports.enterPreview('/dashboard'),false,'repeated recovery must not loop')
now+=16000;assert.equal(exports.enterPreview('/dashboard'),true)
exports.entranceReady();assert.equal(data.size,0)
exports.retryEntrance();assert.equal(reloads,1)

const python=process.env.PYTHON || path.join(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python')
const html=execFileSync(python,['-X','utf8','-c','import sys;sys.path.insert(0,sys.argv[1]);from preview_entry import render_entry;print(render_entry())',path.join(root,'scripts')],{encoding:'utf8'})
const script=html.match(/<script>([\s\S]*)<\/script>/)[1]
async function entry(search,{failure=false,storageFailure=false}={}){
  const calls=[];const storage=new Map();let destination=''
  const status={textContent:''};const retry={hidden:true}
  await vm.runInNewContext(script,{URLSearchParams,AbortController,setTimeout,clearTimeout,
    location:{search,replace:url=>destination=url},
    document:{getElementById:id=>id==='status'?status:retry},
    localStorage:{setItem:(key,value)=>{if(storageFailure)throw new Error('blocked');storage.set(key,value)}},
    fetch:async(url,options)=>{calls.push({url,options});return {ok:!failure,json:async()=>({user:{sessionToken:'synthetic-node-session'}})}}})
  return {calls,storage,destination,status,retry}
}
const normal=await entry('?next=%2Foperations%3Forigin%3Dresume')
assert.equal(normal.calls[0].options.method,'POST')
assert.equal(normal.calls[1].options.headers['X-PM-Session'],'synthetic-node-session')
assert.equal(normal.destination,'/pm-v2/#/operations?origin=resume')
assert.equal(normal.storage.size,1)
const malicious=await entry('?next=https%3A%2F%2Fexample.com%2F')
assert.equal(malicious.destination,'/pm-v2/#/dashboard')
for(const options of [{failure:true},{storageFailure:true}]){
  const failed=await entry('',options)
  assert.equal(failed.destination,'');assert.equal(failed.retry.hidden,false)
  assert.ok(failed.status.textContent.includes('重试'))
}
fs.writeFileSync(path.join(root,'.runtime/test-results/preview-client.json'),JSON.stringify({passed:true,checks:['target route preserved','recovery loop bounded','ready/retry lifecycle','entry POST then authoritative session check','same-origin destination','network/server failure visible','blocked storage visible']},null,2)+'\n')
console.log('Preview entry client checks passed (7 behaviors).')
