import { call, query, type DTO } from './compat'
import type { Category, Project, Requirement, Sprint, Release, Changelog } from '../types'
export const portfolioClient = {
getCategories: () => call<Category[]>('/categories'),
  getCategory: (id: string) => call<Category>('/categories/' + id),
  createCategory: (body: DTO<'CategoryWrite'>) => call<{ id: string; name: string }>('/categories', 'POST', body),
  updateCategory: (id: string, body: DTO<'CategoryWrite'>) => call<Category>('/categories/' + id, 'PUT', body),
  deleteCategory: (id: string) => call<{ ok: number }>('/categories/' + id, 'DELETE'),
  getCategoryProjects: (id: string) => call<Project[]>('/categories/' + id + '/projects'),
  getProjects: () => call<Project[]>('/projects'),
  getProject: (id: string) => call<Project>('/projects/' + id),
  createProject: (body: DTO<'ProjectWrite'>) => call<{ id: string; name: string; initialRequirementId: string }>('/projects', 'POST', body),
  updateProject: (id: string, body: DTO<'ProjectWrite'>) => call<Project>('/projects/' + id, 'PUT', body),
  deleteProject: (id: string) => call<{ ok: number }>('/projects/' + id, 'DELETE'),
  bulkDeleteProjects: (ids: string[]) => call<{ ok: number; deleted: string[]; skipped: unknown[] }>('/projects/bulk-delete', 'POST', { ids }),
}
