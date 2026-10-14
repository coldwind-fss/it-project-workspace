import { call, query, type DTO } from './compat'
import type { Category, Project, Requirement, Sprint, Release, Changelog } from '../types'
export const identityClient = {
  updatePersonnelConfig: (body: DTO<'PersonnelWrite'>) => call<{ ok: number }>('/system/personnel', 'PUT', body),
}
