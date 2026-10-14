// Pure display/import helpers preserving V1 values. No authoritative backend rules.
export const statusLabel: Record<string, string> = { active: '开发中', paused: '暂停中', archived: '已归档', '已排期': '已立项' }

export const statusColors: Record<string, string> = {
  '待处理': '#64748b', '进行中': '#3b82f6', '待交付': '#f59e0b', '已交付': '#10b981',
  '待评估': '#9ca3af', '已立项': '#3b82f6', '需求确认中': '#6366f1', '设计中': '#8b5cf6',
  '开发中': '#f59e0b', '联调中': '#06b6d4', '测试中': '#a855f7', '迭代中': '#0ea5e9',
  '待上线': '#14b8a6', '已上线': '#10b981', '维护中': '#64748b', '暂停中': '#f97316',
  '已关闭': '#6b7280', '已归档': '#94a3b8',
}

export function pColor(p: string) { return { P0: '#ef4444', P1: '#f59e0b', P2: '#3b82f6', P3: '#9ca3af', P4: '#cbd5e1' }[p] || '#9ca3af' }

export function normalizeStatus(s: string) { return statusLabel[s] || s }

export function sColor(s: string) { return statusColors[normalizeStatus(s)] || '#9ca3af' }

export function rColor(s: string) {
  return statusColors[normalizeStatus(s)] || '#9ca3af'
}

export function tColor(t: string) {
  return { '业务确认': '#0ea5e9', '产品设计': '#8b5cf6', '技术建设': '#64748b', '新增功能': '#2563eb', '功能优化': '#f59e0b', '问题修复': '#ef4444', '验证交付': '#14b8a6' }[t] || '#6b7280'
}

export function impactColor(level: string) {
  return ({ 核心: '#dc2626', 重要: '#d97706', 常规: '#64748b' } as Record<string, string>)[level] || '#64748b'
}

export const badgePalette = [
  { bg: '#eff6ff', fg: '#1d4ed8', bd: '#bfdbfe' },
  { bg: '#ecfdf5', fg: '#047857', bd: '#a7f3d0' },
  { bg: '#fff7ed', fg: '#c2410c', bd: '#fed7aa' },
  { bg: '#f5f3ff', fg: '#6d28d9', bd: '#ddd6fe' },
  { bg: '#f0fdfa', fg: '#0f766e', bd: '#99f6e4' },
  { bg: '#fdf2f8', fg: '#be185d', bd: '#fbcfe8' },
  { bg: '#f8fafc', fg: '#475569', bd: '#cbd5e1' },
]

export function hashText(text: string) {
  return Array.from(text || '-').reduce((sum, ch) => sum + ch.charCodeAt(0), 0)
}

export function stableBadgeStyle(text: string, offset = 0) {
  const tone = badgePalette[(hashText(text) + offset) % badgePalette.length]
  return { backgroundColor: tone.bg, color: tone.fg, borderColor: tone.bd }
}

export function personBadgeStyle(name: string) {
  return stableBadgeStyle(name || '-', 0)
}

export function versionBadgeStyle(version: string) {
  return stableBadgeStyle(version || '-', 3)
}

export function splitPeople(value: string) {
  return String(value || '').split(/[,，]/).map(item => item.trim()).filter(Boolean)
}

export function hasPerson(value: string, person: string) {
  return !!person && splitPeople(value).includes(person)
}

export function samePeople(a: string, b: string) {
  const left = splitPeople(a).sort()
  const right = splitPeople(b).sort()
  return left.length === right.length && left.every((item, index) => item === right[index])
}

export function shortDateTime(value: string) {
  return value ? String(value).slice(0, 16) : '-'
}

export function parseTextField(text: string, keys: string[]) {
  for (const key of keys) {
    const match = text.match(new RegExp(`${key}\\s*[：:]\\s*([^\\n]+)`, 'i'))
    if (match?.[1]) return match[1].trim()
  }
  return ''
}

export function guessOption(text: string, options: string[]) {
  return options.find(opt => opt && text.includes(opt)) || ''
}

export function normalizeDateValue(text: string) {
  const match = text.match(/(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})/)
  if (!match) return ''
  const [, y, m, d] = match
  return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`
}

export function progressPercent(p: any) {
  const val = p.progress?.progress ?? p.progress?.currentProgress ?? 0
  return Math.max(0, Math.min(100, Math.round(Number(val) || 0)))
}

export function progressLabel(p: any) {
  return p.progress?.label || ((p.progress?.total || 0) > 0 ? '开发进度' : '暂无需求')
}

export function progressSubLabel(p: any) {
  return p.progress?.subLabel || ((p.progress?.total || 0) > 0 ? '按 L3 状态自动汇总' : '先添加 L3 需求')
}

export function progressCountText(p: any) {
  const pg = p.progress || {}
  if (pg.mode === 'empty' || !pg.total) return '0 项'
  if (pg.mode === 'iteration') return `${pg.currentTotal || 0}/${pg.total || 0}`
  if (pg.mode === 'released') return `${pg.done || 0}/${pg.total || 0}`
  return `${pg.done || 0}/${pg.total || 0}`
}

export function progressBoxClass(p: any) {
  const mode = p.progress?.mode
  if (mode === 'empty') return 'l2-progress-empty'
  if (mode === 'released') return 'l2-progress-released'
  if (mode === 'iteration') return 'l2-progress-iteration'
  return 'l2-progress-active'
}

export function progressTooltip(p: any) {
  const counts = p.progress?.activeStatusCounts || p.progress?.statusCounts || {}
  const detail = Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(' · ')
  return detail || progressSubLabel(p)
}
