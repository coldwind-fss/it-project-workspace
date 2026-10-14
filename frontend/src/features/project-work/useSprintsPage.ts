
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/application-api'
import type { Sprint, Requirement, Release, Project } from '../../types'
export function useSprintsPage() {


const router = useRouter()
const currentSprint = ref<Sprint | null>(null)
const sprints = ref<Sprint[]>([])
const releases = ref<Release[]>([])
const sprintReqs = ref<Requirement[]>([])
const projects = ref<Project[]>([])

const projectColors: Record<string, string> = { p1: '#3b82f6', p2: '#8b5cf6', p3: '#10b981', p4: '#f59e0b' }
function getProjectColor(id: string) { return projectColors[id] || '#6b7280' }

const daysLeft = computed(() => {
  if (!currentSprint.value?.endDate) return '?'
  const d = Math.ceil((new Date(currentSprint.value.endDate).getTime() - Date.now()) / (1000 * 86400))
  return Math.max(0, d)
})

function safeSummary(sum: unknown): string[] {
  if (Array.isArray(sum)) return sum
  if (typeof sum === 'string') { try { const p = JSON.parse(sum); return Array.isArray(p) ? p : [] } catch { return [] } }
  return []
}

onMounted(async () => {
  const [sp, r, p, reqsData] = await Promise.all([
    api.getSprints(),
    api.getReleases(),
    api.getProjects(),
    api.getRequirements({}),
  ])
  if (sp) {
    sprints.value = sp
    currentSprint.value = sp.find((s: any) => s.status === '进行中') || null
  }
  if (r) releases.value = r
  if (p) projects.value = p
  if (reqsData && currentSprint.value) {
    sprintReqs.value = reqsData.filter((req: any) => req.sprintId === currentSprint.value!.id)
  }
})
return { router, currentSprint, sprints, releases, sprintReqs, projects, projectColors, getProjectColor, daysLeft, safeSummary }
}
