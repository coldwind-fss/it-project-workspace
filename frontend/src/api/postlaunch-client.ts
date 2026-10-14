import { get, post, put, del, postMultipart, postDetailed, lifecycleCall, getBlob, download } from "./stage2-transport"
import type { DTO } from "./compat"
export const postlaunchClient = {
// Post-launch operations / management evidence
getPostlaunchOperations: (params?: {
    status?: string;
    department?: string;
    keyword?: string;
}) => {
    const p: string[] = [];
    if (params?.status)
        p.push('status=' + encodeURIComponent(params.status));
    if (params?.department)
        p.push('department=' + encodeURIComponent(params.department));
    if (params?.keyword)
        p.push('keyword=' + encodeURIComponent(params.keyword));
    return get<DTO<"PostlaunchView">[]>('/postlaunch/operations' + (p.length ? '?' + p.join('&') : ''));
},
getPostlaunchOperation: (id: string) => get<DTO<"PostlaunchView">>('/postlaunch/operations/' + id),
createPostlaunchOperation: (data: DTO<"PostlaunchWrite">) => post<DTO<"PostlaunchView">>('/postlaunch/operations', data),
updatePostlaunchOperation: (id: string, data: DTO<"PostlaunchWrite">) => put<DTO<"PostlaunchView">>('/postlaunch/operations/' + id, data),
createPostlaunchIssue: (data: DTO<"PostlaunchIssueWrite">) => post<DTO<"IssueRow">>('/postlaunch/issues', data),
updatePostlaunchIssue: (id: string, data: DTO<"PostlaunchIssueWrite">) => put<DTO<"IssueRow">>('/postlaunch/issues/' + id, data),
createPostlaunchProposal: (data: DTO<"PostlaunchProposalWrite">) => post<DTO<"ProposalRow">>('/postlaunch/proposals', data),
createPostlaunchKnowledge: (data: DTO<"PostlaunchKnowledgeWrite">) => post<DTO<"KnowledgeRow">>('/postlaunch/knowledge', data)
}
