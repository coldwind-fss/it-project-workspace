import { get,post,put,del } from "./stage2-transport"
import type { DTO } from "./compat"
export const insightsClient={
// Dashboard
getDashboardStats: () => get<DTO<"DashboardStats">>('/dashboard/stats'),
getActivities: () => get<DTO<"DashboardActivityView">[]>('/dashboard/activities'),
getDashByCategory: () => get<DTO<"CategoryWork">[]>('/dashboard/bycategory'),
getDashCategorySummary: () => get<DTO<"CategorySummary">[]>('/dashboard/bycategory/summary'),
getWorkReport: (period: 'week' | 'month' = 'week') => get<DTO<"WorkReport">>('/work-reports?period=' + period),
getPostlaunchDashboard: (params?: {
    department?: string;
    keyword?: string;
    period?: string;
    deliveryMonth?: string;
    solutionType?: string;
    lifecycleStage?: string;
    valueStatus?: string;
    businessPriority?: string;
}) => {
    const p: string[] = [];
    if (params?.department)
        p.push('department=' + encodeURIComponent(params.department));
    if (params?.keyword)
        p.push('keyword=' + encodeURIComponent(params.keyword));
    if (params?.period)
        p.push('period=' + encodeURIComponent(params.period));
    if (params?.deliveryMonth)
        p.push('deliveryMonth=' + encodeURIComponent(params.deliveryMonth));
    if (params?.solutionType)
        p.push('solutionType=' + encodeURIComponent(params.solutionType));
    if (params?.lifecycleStage)
        p.push('lifecycleStage=' + encodeURIComponent(params.lifecycleStage));
    if (params?.valueStatus)
        p.push('valueStatus=' + encodeURIComponent(params.valueStatus));
    if (params?.businessPriority)
        p.push('businessPriority=' + encodeURIComponent(params.businessPriority));
    return get<DTO<"PostlaunchDashboard">>('/postlaunch/dashboard' + (p.length ? '?' + p.join('&') : ''));
},
getMyPerformance: (month?: string) => get<DTO<"PerformanceResult">>('/performance/me' + (month ? '?month=' + encodeURIComponent(month) : '')),
saveMyPerformance: (data: DTO<"PerformanceWrite">) => put<DTO<"PerformanceRecord">>('/performance/me', data)
}
