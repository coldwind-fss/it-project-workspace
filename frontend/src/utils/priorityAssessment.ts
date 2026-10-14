export const PRIORITY_ASSESSMENT_VERSION = 'v1'

export type PriorityAssessment = {
  scope?: 'personal' | 'department' | 'multiple' | 'company'
  urgency?: 'normal' | 'month' | 'week' | 'immediate'
  impact?: 'experience' | 'efficiency' | 'blocked' | 'outage'
  blocking?: 'no' | 'yes'
  score?: number
  recommendedPriority?: 'P0' | 'P1' | 'P2' | 'P3' | 'P4'
  projectPriority?: string
  projectCoefficient?: number
  overrideReason?: string
  algorithmVersion?: string
  evaluatedAt?: string
}

const scopeScores = { personal: 5, department: 8, multiple: 12, company: 15 }
const urgencyScores = { normal: 4, month: 8, week: 14, immediate: 20 }
const impactScores = { experience: 5, efficiency: 12, blocked: 22, outage: 30 }
const projectCoefficients: Record<string, number> = { P0: 1.15, P1: 1.08, P2: 1, P3: 0.9, P4: 0.85 }
const priorityRanks: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3, P4: 4 }

export function isPriorityAssessmentComplete(value?: PriorityAssessment | null) {
  return !!(value?.scope && value?.urgency && value?.impact && value?.blocking)
}

export function calculatePriorityAssessment(value: PriorityAssessment, projectPriority = 'P2'): PriorityAssessment {
  const coefficient = projectCoefficients[projectPriority] || 1
  if (!isPriorityAssessmentComplete(value)) {
    return { ...value, projectPriority, projectCoefficient: coefficient, algorithmVersion: PRIORITY_ASSESSMENT_VERSION }
  }
  const base = scopeScores[value.scope!] + urgencyScores[value.urgency!] + impactScores[value.impact!] + (value.blocking === 'yes' ? 15 : 0)
  const score = Math.min(100, Math.round(base * coefficient))
  let recommendedPriority: PriorityAssessment['recommendedPriority']
  if (value.impact === 'outage' && value.urgency === 'immediate') recommendedPriority = 'P0'
  else if (score >= 65) recommendedPriority = 'P1'
  else if (score >= 45) recommendedPriority = 'P2'
  else if (score >= 25) recommendedPriority = 'P3'
  else recommendedPriority = 'P4'
  return {
    ...value,
    score,
    recommendedPriority,
    projectPriority,
    projectCoefficient: coefficient,
    algorithmVersion: PRIORITY_ASSESSMENT_VERSION,
    evaluatedAt: new Date().toISOString(),
  }
}

export function needsPriorityOverrideReason(priority: string, assessment?: PriorityAssessment | null) {
  if (!assessment?.recommendedPriority) return false
  return (priorityRanks[priority] ?? 9) < (priorityRanks[assessment.recommendedPriority] ?? 9)
}
