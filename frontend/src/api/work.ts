import { call, query, type DTO } from './compat'
import type { Category, Project, Requirement, Sprint, Release, Changelog } from '../types'
export const workClient = {
  getRequirements: (params: { type?: string; priority?: string; status?: string; projectId?: string; categoryId?: string } = {}) => call<Requirement[]>('/requirements/live' + query(params)),
  getRequirement: (id: string) => call<Requirement>('/requirements/' + id),
  createRequirement: (body: DTO<'RequirementWrite'>) => call<{ id: string; title: string }>('/requirements', 'POST', body),
  updateRequirement: (id: string, body: DTO<'RequirementWrite'>) => call<Requirement>('/requirements/' + id, 'PUT', body),
  deleteRequirement: (id: string) => call<{ ok: number }>('/requirements/' + id, 'DELETE'),
  bulkDeleteRequirements: (ids: string[]) => call<{ ok: number; deleted: string[]; skipped: unknown[] }>('/requirements/bulk-delete', 'POST', { ids }),
  bulkUpdateRequirementClassification: (ids: string[], body: DTO<'BulkClassification'>) => call<{ ok: number; updated: string[]; skipped: unknown[] }>('/requirements/bulk-classification', 'POST', { ids, ...body }),
  getProjectLifecycleOptions: () => call<{ solutionTypes: { key: string; label: string; description: string }[]; itemKinds: { key: string; label: string }[]; phaseStatuses: { key: string; label: string }[]; templates: Record<string, unknown[]> }>('/project-lifecycle/options'),
  getRequirementPhases: (id: string) => call<unknown[]>('/requirements/' + id + '/phases'),
  createRequirementPhase: (id: string, body: DTO<'PhaseWrite'>) => call<Record<string, unknown>>('/requirements/' + id + '/phases', 'POST', body),
  updateRequirementPhase: (id: string, phaseId: string, body: DTO<'PhaseWrite'>) => call<Record<string, unknown>>('/requirements/' + id + '/phases/' + phaseId, 'PUT', body),
  getRequirementWorkLogs: (id: string) => call<unknown[]>('/requirements/' + id + '/work-logs'),
  createRequirementWorkLog: (id: string, body: DTO<'WorkLogWrite'>) => call<Record<string, unknown>>('/requirements/' + id + '/work-logs', 'POST', body),
  getSprints: () => call<Sprint[]>('/sprints'),
  getReleases: () => call<Release[]>('/releases'),
  getChangelogs: () => call<Changelog[]>('/changelogs'),
  getRequirementChangelogs: (id: string) => call<Changelog[]>('/requirements/' + id + '/changelogs'),
}
