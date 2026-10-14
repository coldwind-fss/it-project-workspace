import { API_BASE, sessionHeaders } from './transport'
const BASE = API_BASE

async function lifecycleCall(path: string, method = 'GET', body?: any, token = '') {
  const headers: Record<string, string> = token ? { 'X-PM-Collaboration-Token': token } : authHeaders()
  const multipart = body instanceof FormData
  if (body && !multipart) headers['Content-Type'] = 'application/json'
  const response = await fetch(BASE + path, { method, headers, cache: 'no-store',
    body: body ? multipart ? body : JSON.stringify(body) : undefined })
  const raw = await response.text()
  let result: any = null
  try { result = raw ? JSON.parse(raw) : null } catch {
    result = { detail: raw || `请求失败（HTTP ${response.status}）` }
  }
  if (!response.ok) throw new Error(result.detail || result.error || '保存失败，请重试')
  return result
}

function encodeHeader(value: string) {
  if (!value) return ''
  try {
    return btoa(unescape(encodeURIComponent(value)))
  } catch {
    return ''
  }
}

function authHeaders(extra?: Record<string, string>) { return sessionHeaders(extra) }

export function reportClientLog(level: string, message: string, detail?: any) {
  try {
    const payload = JSON.stringify({
      level,
      message: String(message || '').slice(0, 1000),
      source: 'frontend',
      path: window.location.href.replace(/([?&](?:token|entryToken|reviewToken)=)[^&#]*/gi, '$1[redacted]'),
      userAgent: navigator.userAgent,
      detail: detail ? JSON.stringify(detail).slice(0, 5000) : '',
    })
    const blob = new Blob([payload], { type: 'application/json' })
    if (navigator.sendBeacon) {
      navigator.sendBeacon(BASE + '/app-logs', blob)
      return
    }
    fetch(BASE + '/app-logs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: payload, keepalive: true })
  } catch {}
}

async function get<T = any>(path: string): Promise<T | null> {
  try {
    const sep = path.includes('?') ? '&' : '?'
    const url = BASE + path + sep + '_t=' + Date.now()
    const r = await fetch(url, { headers: authHeaders({ 'Cache-Control': 'no-cache', Pragma: 'no-cache' }), cache: 'no-store' })
    if (!r.ok) { console.error('API:', path, r.status); reportClientLog('error', 'GET API failed', { path, status: r.status }); return null }
    return await r.json()
  } catch (e: any) { console.error('Fetch:', path, e); reportClientLog('error', 'GET fetch exception', { path, error: e?.message || String(e) }); return null }
}

async function getBlob(path: string): Promise<Blob | null> {
  try {
    const r = await fetch(BASE + path, { headers: authHeaders({ 'Cache-Control': 'no-cache' }), cache: 'no-store' })
    if (!r.ok) {
      console.error('API:', path, r.status)
      reportClientLog('error', 'GET blob API failed', { path, status: r.status })
      return null
    }
    return await r.blob()
  } catch (e: any) {
    console.error('Fetch:', path, e)
    reportClientLog('error', 'GET blob fetch exception', { path, error: e?.message || String(e) })
    return null
  }
}

async function del(path: string) {
  try {
    const r = await fetch(BASE + path, { method: 'DELETE', headers: authHeaders() })
    const data = await r.json().catch(() => null)
    if (!r.ok) { console.error('API:', path, r.status, data); reportClientLog('error', 'DELETE API failed', { path, status: r.status, data }); return null }
    return data
  }
  catch (e: any) { console.error(e); reportClientLog('error', 'DELETE fetch exception', { path, error: e?.message || String(e) }); return null }
}

async function post(path: string, body: any) {
  try {
    const r = await fetch(BASE + path, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(body) })
    const data = await r.json().catch(() => null)
    if (!r.ok) { console.error('API:', path, r.status, data); reportClientLog('error', 'POST API failed', { path, status: r.status, data }); return null }
    return data
  } catch (e: any) { console.error(e); reportClientLog('error', 'POST fetch exception', { path, error: e?.message || String(e) }); return null }
}

// Conversion is a gated workflow action.  Keep the server error so the form
// can explain why the next step did not start instead of appearing inert.
async function postDetailed(path: string, body: any) {
  try {
    const r = await fetch(BASE + path, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(body) })
    const data = await r.json().catch(() => null)
    if (!r.ok) {
      console.error('API:', path, r.status, data)
      reportClientLog('error', 'POST workflow API failed', { path, status: r.status, data })
      return { ...(data || {}), _failed: true, status: r.status }
    }
    return data
  } catch (e: any) {
    console.error(e)
    reportClientLog('error', 'POST workflow fetch exception', { path, error: e?.message || String(e) })
    return { _failed: true, error: '网络请求失败，请刷新页面后重试' }
  }
}

async function postMultipart(path: string, body: FormData) {
  try {
    const r = await fetch(BASE + path, { method: 'POST', headers: authHeaders(), body })
    const data = await r.json().catch(() => null)
    if (!r.ok) { console.error('API:', path, r.status, data); reportClientLog('error', 'POST multipart API failed', { path, status: r.status, data }); return null }
    return data
  } catch (e: any) { console.error(e); reportClientLog('error', 'POST multipart fetch exception', { path, error: e?.message || String(e) }); return null }
}

async function put(path: string, body: any) {
  try {
    const r = await fetch(BASE + path, { method: 'PUT', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(body) })
    const data = await r.json().catch(() => null)
    if (!r.ok) { console.error('API:', path, r.status, data); reportClientLog('error', 'PUT API failed', { path, status: r.status, data }); return null }
    return data
  } catch (e: any) { console.error(e); reportClientLog('error', 'PUT fetch exception', { path, error: e?.message || String(e) }); return null }
}

export const api = {
  getRequirementLifecycle: (id: string) => lifecycleCall('/requirements/' + id + '/lifecycle'),
  getDeliveryBaselines: (id: string) => lifecycleCall('/requirements/' + id + '/delivery-baselines'),
  createDeliveryBaseline: (id: string, data: any) => lifecycleCall('/requirements/' + id + '/delivery-baselines', 'POST', data),
  createCollaborationLink: (id: string, data: any) => lifecycleCall('/requirements/' + id + '/collaboration-links', 'POST', data),
  revokeCollaborationLink: (id: string) => lifecycleCall('/collaboration-links/' + id + '/revoke', 'POST'),
  deliverRequirement: (id: string, data: any) => lifecycleCall('/requirements/' + id + '/deliveries', 'POST', data),
  routeDeliveryFeedback: (id: string, routeType: string) => lifecycleCall('/delivery-feedback/' + id + '/route', 'POST', { routeType }),
  getCollaborationLinkContext: (token: string) => lifecycleCall('/collaboration-link/context', 'GET', undefined, token),
  submitCollaborationLink: (token: string, data: any) => lifecycleCall('/collaboration-link/submit', 'POST', data, token),
  uploadCollaborationLinkFile: (token: string, file: File, key: string) => {
    const data = new FormData(); data.append('file', file); data.append('uploadKey', key)
    return lifecycleCall('/collaboration-link/attachments', 'POST', data, token)
  },
  downloadCollaborationLinkFile: async (token: string, id: string) => {
    const response = await fetch(BASE + '/collaboration-link/attachments/' + id, { headers: { 'X-PM-Collaboration-Token': token }, cache: 'no-store' })
    if (!response.ok) throw new Error('附件不存在、未授权或链接已失效')
    return response.blob()
  },
  get, post, put, del,

  // Categories (L1)
  getCategories: () => get('/categories'),
  getCategory: (id: string) => get('/categories/' + id),
  getCategoryProjects: (id: string) => get('/categories/' + id + '/projects'),
  createCategory: (data: any) => post('/categories', data),
  updateCategory: (id: string, data: any) => put('/categories/' + id, data),
  deleteCategory: (id: string) => del('/categories/' + id),

  // Projects (L2)
  getProjects: () => get('/projects'),
  getProject: (id: string) => get('/projects/' + id),
  getProjectLifecycleOptions: () => get('/project-lifecycle/options'),
  createProject: (data: any) => post('/projects', data),
  updateProject: (id: string, data: any) => put('/projects/' + id, data),
  deleteProject: (id: string) => del('/projects/' + id),
  bulkDeleteProjects: (ids: string[]) => post('/projects/bulk-delete', { ids }),

  // Requirements (L3)
  getRequirements: (params?: { type?: string; priority?: string; status?: string; projectId?: string; categoryId?: string }) => {
    let qs = ''
    if (params) {
      const p: string[] = []
      if (params.type && params.type !== '全部') p.push('type=' + params.type)
      if (params.priority && params.priority !== '全部') p.push('priority=' + params.priority)
      if (params.status && params.status !== '全部') p.push('status=' + params.status)
      if (params.projectId) p.push('projectId=' + params.projectId)
      if (params.categoryId) p.push('categoryId=' + params.categoryId)
      if (p.length) qs = '?' + p.join('&')
    }
    // Use a cache-busting route as well as a timestamp. Some DingTalk/webview
    // layers cache filtered URLs without honoring query-string changes.
    return get('/requirements/live' + qs)
  },
  getRequirement: (id: string) => get('/requirements/' + id),
  createRequirement: (data: any) => post('/requirements', data),
  updateRequirement: (id: string, data: any) => put('/requirements/' + id, data),
  deleteRequirement: (id: string) => del('/requirements/' + id),
  getRequirementWorkLogs: (id: string) => get('/requirements/' + id + '/work-logs'),
  createRequirementWorkLog: (id: string, data: any) => post('/requirements/' + id + '/work-logs', data),
  getRequirementPhases: (id: string) => get('/requirements/' + id + '/phases'),
  createRequirementPhase: (id: string, data: any) => post('/requirements/' + id + '/phases', data),
  updateRequirementPhase: (id: string, phaseId: string, data: any) => put('/requirements/' + id + '/phases/' + phaseId, data),
  getRequirementSharedActivities: (id: string) => get('/requirements/' + id + '/shared-activities'),
  createRequirementSharedActivity: (id: string, data: any) => post('/requirements/' + id + '/shared-activities', data),
  getProjectSharedActivities: (id: string) => get('/projects/' + id + '/shared-activities'),
  createProjectSharedActivity: (id: string, data: any) => post('/projects/' + id + '/shared-activities', data),
  getSharedActivityComments: (id: string) => get('/shared-activities/' + id + '/comments'),
  createSharedActivityComment: (id: string, data: any) => post('/shared-activities/' + id + '/comments', data),
  getWorkIntakeSchema: () => get('/work-intake/schema'),
  workIntake: (data: any) => post('/work-intake', data),
  getWorkIntakeBatch: (id: string) => get('/work-intake/' + id),
  rollbackWorkIntake: (id: string) => post('/work-intake/' + id + '/rollback', {}),
  getBusinessRequestOptions: () => get('/business-requests/options'),
  getBusinessRequests: (status?: string) => get('/business-requests' + (status ? '?status=' + encodeURIComponent(status) : '')),
  createBusinessRequest: (data: any) => post('/business-requests', data),
  updateBusinessRequest: (id: string, data: any) => put('/business-requests/' + id, data),
  getDemandPoolOptions: () => get('/demand-pool/options'),
  getDemandPool: (params?: { status?: string; department?: string }) => {
    const p: string[] = []
    if (params?.status) p.push('status=' + encodeURIComponent(params.status))
    if (params?.department) p.push('department=' + encodeURIComponent(params.department))
    return get('/demand-pool' + (p.length ? '?' + p.join('&') : ''))
  },
  getDemandPoolItem: (id: string) => get('/demand-pool/' + id),
  createDemandPoolItem: (data: any) => post('/demand-pool', data),
  updateDemandPoolItem: (id: string, data: any) => put('/demand-pool/' + id, data),
  saveDemandPoolDecomposition: (id: string, data: any) => put('/demand-pool/' + id + '/decomposition', data),
  historicalDecomposeDemandPool: (id: string, data: any) => postDetailed('/demand-pool/' + id + '/historical-decomposition', data),
  saveDemandPoolBranchDecisions: (id: string, data: any) => put('/demand-pool/' + id + '/branch-decisions', data),
  deleteDemandPoolItem: (id: string) => del('/demand-pool/' + id),
  createDemandPoolConfirmation: (id: string, data?: any) => post('/demand-pool/' + id + '/confirmations', data || {}),
  resendDemandPoolConfirmation: (id: string) => postDetailed('/demand-pool/' + id + '/confirmations/resend', {}),
  getDemandPoolConfirmation: (id: string) => get('/demand-pool-confirmations/' + id),
  submitDemandPoolConfirmation: (id: string, data: any) => post('/demand-pool-confirmations/' + id, data),
  getDemandPoolConfirmationByToken: (token: string) => get('/demand-pool-confirmations/by-token?token=' + encodeURIComponent(token)),
  submitDemandPoolConfirmationByToken: (token: string, data: any) => post('/demand-pool-confirmations/by-token', { ...data, token }),
  convertDemandPool: (id: string, data: any) => postDetailed('/demand-pool/' + id + '/convert', data),
  getDemandPoolNotifications: () => get('/demand-pool/notifications'),
  updateDemandPoolNotification: (id: string, data: any) => put('/demand-pool/notifications/' + id, data),
  getDemandPoolEntryContext: (token: string) => get('/demand-pool/entry-context?token=' + encodeURIComponent(token)),
  sendDemandPoolNotification: (data: any) => post('/demand-pool/notifications', data),
  submitDemandCollectionResponse: (data: any) => post('/demand-collections/responses', data),
  getDemandCollectionBatches: () => get('/demand-collections/batches'),
  getDemandCollectionBatch: (id: string) => get('/demand-collections/batches/' + id),
  retryDemandCollectionFailures: (id: string) => post('/demand-collections/batches/' + id + '/retry-failures', {}),
  getDemandCollectionResponse: (id: string) => get('/demand-collections/responses/' + id),
  judgeDemandCollectionResponse: (id: string, data: any) => put('/demand-collections/responses/' + id, data),
  submitDemandPoolMaterials: (data: any) => post('/demand-pool/materials', data),
  assignDemandPoolReviews: (id: string, data: any) => post('/demand-pool/' + id + '/reviews', data),
  reuseDemandPoolBusinessReview: (id: string, data: any) => postDetailed('/demand-pool/' + id + '/reviews/reuse', data),
  getDemandPoolReview: (id: string) => get('/demand-pool-reviews/' + id),
  submitDemandPoolReview: (id: string, data: any) => post('/demand-pool-reviews/' + id, data),
  getDemandPoolReviewByToken: (token: string) => get('/demand-pool-reviews/by-token?token=' + encodeURIComponent(token)),
  submitDemandPoolReviewByToken: (token: string, data: any) => post('/demand-pool-reviews/by-token', { ...data, token }),
  getDemandPoolSupplements: (id: string) => get('/demand-pool/' + id + '/supplements'),
  getDemandPoolSupplement: (id: string) => get('/demand-pool-supplements/' + id),
  createDemandPoolSupplement: (id: string, data: any) => post('/demand-pool/' + id + '/supplements', data),
  submitDemandPoolSupplement: (id: string, data: any) => put('/demand-pool-supplements/' + id, data),
  getDemandPoolPocs: (id: string) => get('/demand-pool/' + id + '/pocs'),
  createDemandPoolPoc: (id: string, data: any) => post('/demand-pool/' + id + '/pocs', data),
  updateDemandPoolPoc: (id: string, data: any) => put('/demand-pool-pocs/' + id, data),
  getPocWorkbenchOptions: () => get('/poc-workbench/options'),
  getPocWorkbenchRecords: (params?: { recordType?: string; status?: string; keyword?: string; projectId?: string; requirementId?: string }) => {
    const p: string[] = []
    if (params?.recordType) p.push('recordType=' + encodeURIComponent(params.recordType))
    if (params?.status) p.push('status=' + encodeURIComponent(params.status))
    if (params?.keyword) p.push('keyword=' + encodeURIComponent(params.keyword))
    if (params?.projectId) p.push('projectId=' + encodeURIComponent(params.projectId))
    if (params?.requirementId) p.push('requirementId=' + encodeURIComponent(params.requirementId))
    return get('/poc-workbench/records' + (p.length ? '?' + p.join('&') : ''))
  },
  getPocWorkbenchRecord: (id: string) => get('/poc-workbench/records/' + encodeURIComponent(id)),
  createPocWorkbenchRecord: (data: any) => post('/poc-workbench/records', data),
  updatePocWorkbenchRecord: (id: string, data: any) => put('/poc-workbench/records/' + encodeURIComponent(id), data),
  derivePocWorkbenchCapability: (id: string, data?: any) => post('/poc-workbench/records/' + encodeURIComponent(id) + '/derive-capability', data || {}),
  getDemandPoolValueCard: (id: string) => get('/demand-pool/' + id + '/value-card'),
  saveDemandPoolValueCard: (id: string, data: any) => put('/demand-pool/' + id + '/value-card', data),
  getDemandPoolOutcomeRequests: (id: string) => get('/demand-pool/' + id + '/outcome-requests'),
  createDemandPoolOutcomeRequest: (id: string, data: any) => post('/demand-pool/' + id + '/outcome-requests', data),
  getRequirementOutcomeRequests: (id: string) => get('/requirements/' + id + '/outcome-requests'),
  createRequirementOutcomeRequest: (id: string, data: any) => post('/requirements/' + id + '/outcome-requests', data),
  getProjectOutcomeRequests: (id: string) => get('/projects/' + id + '/outcome-requests'),
  createProjectOutcomeRequest: (id: string, data: any) => post('/projects/' + id + '/outcome-requests', data),
  getDemandPoolOutcomeContext: (token: string) => get('/demand-pool-outcome-context?token=' + encodeURIComponent(token)),
  submitDemandPoolOutcome: (data: any) => post('/demand-pool-outcome-submit', data),
  sendDemandPoolOutcomeRequest: (id: string) => post('/demand-pool-value-requests/' + id + '/send', {}),
  markDemandPoolOutcomeViewed: (id: string) => post('/demand-pool-value-requests/' + id + '/view', {}),
  getBusinessCollaborations: (status?: string) => get('/business-collaborations' + (status ? '?status=' + encodeURIComponent(status) : '')),
  createBusinessCollaboration: (data: any) => post('/business-collaborations', data),
  updateBusinessCollaboration: (id: string, data: any) => put('/business-collaborations/' + id, data),
  getRequirementBusinessCollaborations: (id: string) => get('/requirements/' + id + '/business-collaborations'),
  createRequirementBusinessCollaboration: (id: string, data: any) => post('/requirements/' + id + '/business-collaborations', data),
  getBusinessCollaborationMessages: (id: string) => get('/business-collaborations/' + id + '/messages'),
  createBusinessCollaborationMessage: (id: string, data: any) => post('/business-collaborations/' + id + '/messages', data),
  uploadBusinessAttachment: (ownerType: string, ownerId: string, file: File, entryToken = '') => {
    const body = new FormData()
    body.append('ownerType', ownerType)
    body.append('ownerId', ownerId)
    if (entryToken) body.append('entryToken', entryToken)
    body.append('file', file, file.name)
    return postMultipart('/business-attachments', body)
  },
  getBusinessAttachmentBlob: (id: string) => getBlob('/business-attachments/' + id + '/download'),
  deleteBusinessAttachment: (id: string) => del('/business-attachments/' + id),
  bulkDeleteRequirements: (ids: string[]) => post('/requirements/bulk-delete', { ids }),
  bulkUpdateRequirementClassification: (ids: string[], data: any) => post('/requirements/bulk-classification', { ids, ...data }),
  getRecycleBin: () => get('/recycle-bin'),
  restoreRecycleItem: (type: string, id: string) => post(`/recycle-bin/${type}/${id}/restore`, {}),
  purgeRecycleItem: (type: string, id: string) => del(`/recycle-bin/${type}/${id}`),
  getRequirementChangelogs: (id: string) => get('/requirements/' + id + '/changelogs'),

  // Todos
  getTodos: (status?: string) => get('/todos' + (status ? '?status=' + encodeURIComponent(status) : '')),
  getTodoUnreadCount: () => get('/todos/unread-count'),
  markTodoRead: (id: string) => put('/todos/' + id + '/read', {}),
  markTodoDone: (id: string) => put('/todos/' + id + '/done', {}),

  // Sprints
  getSprints: () => get('/sprints'),
  getSprint: (id: string) => get('/sprints/' + id),
  getCurrentSprint: () => get('/sprints/current'),
  createSprint: (data: any) => post('/sprints', data),
  updateSprint: (id: string, data: any) => put('/sprints/' + id, data),
  deleteSprint: (id: string) => del('/sprints/' + id),

  // Changelogs
  getChangelogs: (projectId?: string) => {
    let qs = projectId ? '?projectId=' + projectId : ''
    return get('/changelogs' + qs)
  },
  createChangelog: (data: any) => post('/changelogs', data),

  // Releases
  getReleases: (projectId?: string) => {
    let qs = projectId ? '?projectId=' + projectId : ''
    return get('/releases' + qs)
  },
  createRelease: (data: any) => post('/releases', data),

  // Dashboard
  getDashboardStats: () => get('/dashboard/stats'),
  getActivities: () => get('/dashboard/activities'),
  getDashByCategory: () => get('/dashboard/bycategory'),
  getDashCategorySummary: () => get('/dashboard/bycategory/summary'),
  getWorkReport: (period: 'week' | 'month' = 'week') => get('/work-reports?period=' + period),

  // Post-launch operations / management evidence
  getPostlaunchOperations: (params?: { status?: string; department?: string; keyword?: string }) => {
    const p: string[] = []
    if (params?.status) p.push('status=' + encodeURIComponent(params.status))
    if (params?.department) p.push('department=' + encodeURIComponent(params.department))
    if (params?.keyword) p.push('keyword=' + encodeURIComponent(params.keyword))
    return get('/postlaunch/operations' + (p.length ? '?' + p.join('&') : ''))
  },
  getPostlaunchOperation: (id: string) => get('/postlaunch/operations/' + id),
  createPostlaunchOperation: (data: any) => post('/postlaunch/operations', data),
  updatePostlaunchOperation: (id: string, data: any) => put('/postlaunch/operations/' + id, data),
  getPostlaunchDashboard: (params?: { department?: string; keyword?: string; period?: string; deliveryMonth?: string; solutionType?: string; lifecycleStage?: string; valueStatus?: string; businessPriority?: string }) => {
    const p: string[] = []
    if (params?.department) p.push('department=' + encodeURIComponent(params.department))
    if (params?.keyword) p.push('keyword=' + encodeURIComponent(params.keyword))
    if (params?.period) p.push('period=' + encodeURIComponent(params.period))
    if (params?.deliveryMonth) p.push('deliveryMonth=' + encodeURIComponent(params.deliveryMonth))
    if (params?.solutionType) p.push('solutionType=' + encodeURIComponent(params.solutionType))
    if (params?.lifecycleStage) p.push('lifecycleStage=' + encodeURIComponent(params.lifecycleStage))
    if (params?.valueStatus) p.push('valueStatus=' + encodeURIComponent(params.valueStatus))
    if (params?.businessPriority) p.push('businessPriority=' + encodeURIComponent(params.businessPriority))
    return get('/postlaunch/dashboard' + (p.length ? '?' + p.join('&') : ''))
  },
  createPostlaunchIssue: (data: any) => post('/postlaunch/issues', data),
  updatePostlaunchIssue: (id: string, data: any) => put('/postlaunch/issues/' + id, data),
  createPostlaunchProposal: (data: any) => post('/postlaunch/proposals', data),
  createPostlaunchKnowledge: (data: any) => post('/postlaunch/knowledge', data),
  getMyPerformance: (month?: string) => get('/performance/me' + (month ? '?month=' + encodeURIComponent(month) : '')),
  saveMyPerformance: (data: any) => put('/performance/me', data),

  // DingTalk
  getDingTalkConfig: () => get('/dingtalk/config'),
  loginWithDingTalk: (authCode: string) => post('/dingtalk/login', { authCode }),
  getDingTalkOptions: () => get('/dingtalk/options'),

  // Notifications
  getNotificationTargets: () => get('/notification/targets'),
  getNotificationDeliveries: (limit = 50) => get('/notification/deliveries?limit=' + encodeURIComponent(String(limit))),
  createNotificationTarget: (data: any) => post('/notification/targets', data),
  updateNotificationTarget: (id: string, data: any) => put('/notification/targets/' + id, data),
  deleteNotificationTarget: (id: string) => del('/notification/targets/' + id),
  getNotificationPreview: (data: any) => post('/notification/preview', data),
  syncNotification: (data: any) => post('/notification/sync', data),

  // Operation records
  getOperations: (params?: { entityType?: string; action?: string; keyword?: string }) => {
    const p: string[] = []
    if (params?.entityType) p.push('entityType=' + encodeURIComponent(params.entityType))
    if (params?.action) p.push('action=' + encodeURIComponent(params.action))
    if (params?.keyword) p.push('keyword=' + encodeURIComponent(params.keyword))
    return get('/operations' + (p.length ? '?' + p.join('&') : ''))
  },

  getAppLogs: (params?: { level?: string; source?: string; limit?: number }) => {
    const p: string[] = []
    if (params?.level) p.push('level=' + encodeURIComponent(params.level))
    if (params?.source) p.push('source=' + encodeURIComponent(params.source))
    if (params?.limit) p.push('limit=' + encodeURIComponent(String(params.limit)))
    return get('/app-logs' + (p.length ? '?' + p.join('&') : ''))
  },

  // System management
  getPersonnelConfig: () => get('/system/personnel'),
  updatePersonnelConfig: (data: any) => put('/system/personnel', data),
}
