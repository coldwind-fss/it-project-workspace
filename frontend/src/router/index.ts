import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '../components/Layout.vue'
import { refreshSessionAccess,canVisitPage,firstAllowedPage,sessionAccessError } from '../features/access/session-access'
import { PREVIEW_ENTRY,entranceProblem,enterPreview,entranceReady } from '../features/access/preview-entry'
import { ApiError } from '../api/transport'
import { showFeedback } from '../utils/feedback'

const routes: RouteRecordRaw[] = [
  { path: '/entry/collaboration', name: 'CollaborationLinkEntry', component: () => import('../pages/CollaborationLinkEntry.vue') },
  {
    path: '/collaboration-upload',
    name: 'CollaborationUpload',
    component: () => import('../pages/CollaborationUpload.vue'),
  },
  {
    path: '/entry/demand',
    name: 'DemandEntry',
    component: () => import('../pages/DemandEntry.vue'),
  },
  {
    path: '/entry/demand-confirm',
    name: 'DemandConfirmEntry',
    component: () => import('../pages/DemandConfirmEntry.vue'),
  },
  {
    path: '/entry/demand-outcome',
    name: 'DemandOutcomeEntry',
    component: () => import('../pages/DemandOutcomeEntry.vue'),
  },
  {
    path: '/entry/demand-review',
    name: 'DemandReviewEntry',
    component: () => import('../pages/DemandReviewEntry.vue'),
  },
  {
    path: '/entry/demand-supplement',
    name: 'DemandSupplementEntry',
    component: () => import('../pages/DemandSupplementEntry.vue'),
  },
  {
    path: '/entry/demand-poc',
    name: 'DemandPocEntry',
    component: () => import('../pages/DemandPocEntry.vue'),
  },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('../pages/DashboardOverview.vue') },
      { path: 'postlaunch/operations', name: 'PostlaunchOperations', component: () => import('../pages/PostLaunchOperations.vue') },
      { path: 'postlaunch/dashboard', name: 'PostlaunchDashboard', component: () => import('../pages/PostLaunchDashboard.vue') },
      // Keep the old URL working for existing bookmarks. It now lands on the
      // management dashboard, while execution records have their own route.
      { path: 'operations-dashboard', name: 'OperationsDashboardLegacy', redirect: '/postlaunch/dashboard' },
      { path: 'performance', name: 'PerformanceWorkbench', component: () => import('../pages/PerformanceWorkbench.vue') },
      { path: 'products', name: 'ProductOverview', component: () => import('../pages/ProductOverview.vue') },
      { path: 'poc-workbench', name: 'PocWorkbench', component: () => import('../pages/PocWorkbench.vue') },
      { path: 'management', redirect: '/dashboard' },
      { path: 'requirements', name: 'Requirements', component: () => import('../pages/RequirementsList.vue') },
      { path: 'requirements/kanban', name: 'Kanban', redirect: '/products?view=work' },
      { path: 'requirements/:id', name: 'RequirementDetail', component: () => import('../pages/RequirementDetail.vue') },
      { path: 'projects/:id', name: 'ProjectDetail', component: () => import('../pages/ProjectDetail.vue') },
      { path: 'sprints', name: 'Sprints', component: () => import('../pages/Sprints.vue') },
      { path: 'changelog', name: 'Changelog', component: () => import('../pages/Changelog.vue') },
      { path: 'knowledge', name: 'KnowledgeBase', component: () => import('../pages/KnowledgeBase.vue') },
      { path: 'workspace', name: 'Workspace', component: () => import('../pages/Workspace.vue') },
      { path: 'intake', name: 'BusinessIntake', component: () => import('../pages/BusinessIntake.vue') },
      { path: 'demand-pool', name: 'DemandPool', component: () => import('../pages/DemandPool.vue') },
      // Keep legacy bookmarks and DingTalk links resolvable, but make the
      // workbench the only visible personal action surface.
      { path: 'todos', name: 'TodoCenterLegacy', redirect: to => ({ path: '/workspace', query: { ...to.query, focus: 'pending' } }) },
      { path: 'notifications', name: 'NotificationSettings', component: () => import('../pages/NotificationSettings.vue') },
      { path: 'operations', name: 'OperationRecords', component: () => import('../pages/OperationRecords.vue') },
      { path: 'system', name: 'SystemManagement', component: () => import('../pages/SystemManagement.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// A DingTalk/Feishu webview can keep an older index.html while the server has
// already published a newer set of hashed lazy chunks.  Vue Router rejects
// the navigation when such a chunk cannot be imported, which otherwise looks
// like a completely blank page.  Retry the current URL once with a fresh
// query-string so the webview fetches the latest entry point; if it still
// fails, App.vue renders a visible recovery action instead of a blank shell.
router.onError(error => {
  const message = String((error as Error)?.message || error || '')
  const isChunkLoadError = /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk|ChunkLoadError/i.test(message)
  if (!isChunkLoadError) return
  try {
    const key = 'pm-route-chunk-recovery'
    if (sessionStorage.getItem(key) === '1') return
    sessionStorage.setItem(key, '1')
    const url = new URL(window.location.href)
    url.searchParams.set('_pm_route_reload', String(Date.now()))
    window.location.replace(url.toString())
  } catch {}
})

router.afterEach(() => {
  try {
    sessionStorage.removeItem('pm-route-chunk-recovery')
    sessionStorage.removeItem('pm-vite-preload-recovery')
  } catch {}
})

router.beforeEach(async to => {
  let user: any = {}
  try { user = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch {}
  // Keep the route out of every other user's navigation and block direct
  // hash-URL entry as soon as the local DingTalk identity is known.  The API
  // performs the authoritative check as well, so clearing localStorage cannot
  // expose another person's records.
  if(to.path.startsWith('/entry/')||to.path==='/collaboration-upload')return true
  if(!user?.sessionToken){
    if(PREVIEW_ENTRY){
      if(enterPreview(to.fullPath))return false
      entranceProblem.value='无法建立演示会话，请重新进入系统。'
    }
    return true
  }
  const access=await refreshSessionAccess()
  if(!access){
    if(PREVIEW_ENTRY){
      if(sessionAccessError.value instanceof ApiError&&sessionAccessError.value.status===401&&enterPreview(to.fullPath))return false
      entranceProblem.value='暂时无法连接系统或验证会话，请检查网络后重试。'
    }
    return true
  }
  entranceReady()
  if(!canVisitPage(to.path)){
    showFeedback('当前角色没有此页面权限',{kind:'error'})
    const next=firstAllowedPage()
    return next&&next!==to.path?next:false
  }
  // Page aliases use the existing role configuration; API action/resource checks remain authoritative.
  if (to.path === '/system' && access.role !== 'super_admin') return firstAllowedPage()||false
  return true
})

export default router
