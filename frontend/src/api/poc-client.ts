import { get,post,put,del } from "./stage2-transport"
import type { DTO } from "./compat"
export const pocClient={
getPocWorkbenchOptions: () => get<DTO<"PocOptions">>('/poc-workbench/options'),
getPocWorkbenchRecords: (params?: {
    recordType?: string;
    status?: string;
    keyword?: string;
    projectId?: string;
    requirementId?: string;
}) => {
    const p: string[] = [];
    if (params?.recordType)
        p.push('recordType=' + encodeURIComponent(params.recordType));
    if (params?.status)
        p.push('status=' + encodeURIComponent(params.status));
    if (params?.keyword)
        p.push('keyword=' + encodeURIComponent(params.keyword));
    if (params?.projectId)
        p.push('projectId=' + encodeURIComponent(params.projectId));
    if (params?.requirementId)
        p.push('requirementId=' + encodeURIComponent(params.requirementId));
    return get<DTO<"PocView">[]>('/poc-workbench/records' + (p.length ? '?' + p.join('&') : ''));
},
getPocWorkbenchRecord: (id: string) => get<DTO<"PocView">>('/poc-workbench/records/' + encodeURIComponent(id)),
createPocWorkbenchRecord: (data: DTO<"PocWrite">) => post<DTO<"PocView">>('/poc-workbench/records', data),
updatePocWorkbenchRecord: (id: string, data: DTO<"PocWrite">) => put<DTO<"PocView">>('/poc-workbench/records/' + encodeURIComponent(id), data),
derivePocWorkbenchCapability: (id: string, data?: DTO<"DeriveWrite">) => post<DTO<"PocView">>('/poc-workbench/records/' + encodeURIComponent(id) + '/derive-capability', data || {})
}
