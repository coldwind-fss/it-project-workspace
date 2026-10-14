import { get, post, put, del, postMultipart, postDetailed, lifecycleCall, getBlob, download } from "./stage2-transport"
import type { DTO } from "./compat"
export const valueClient = {
getDemandPoolValueCard: (id: string) => get<DTO<"ValueCardView">>('/demand-pool/' + id + '/value-card'),
saveDemandPoolValueCard: (id: string, data: DTO<"ValueCardWrite">) => put<DTO<"ValueCardView">>('/demand-pool/' + id + '/value-card', data),
getDemandPoolOutcomeRequests: (id: string) => get<DTO<"ValueRequestView">[]>('/demand-pool/' + id + '/outcome-requests'),
createDemandPoolOutcomeRequest: (id: string, data: DTO<"OutcomeRequestWrite">) => post<DTO<"ValueRequestView">>('/demand-pool/' + id + '/outcome-requests', data),
getRequirementOutcomeRequests: (id: string) => get<DTO<"ValueRequestView">[]>('/requirements/' + id + '/outcome-requests'),
createRequirementOutcomeRequest: (id: string, data: DTO<"OutcomeRequestWrite">) => post<DTO<"ValueRequestView">>('/requirements/' + id + '/outcome-requests', data),
getProjectOutcomeRequests: (id: string) => get<DTO<"ValueRequestView">[]>('/projects/' + id + '/outcome-requests'),
createProjectOutcomeRequest: (id: string, data: DTO<"OutcomeRequestWrite">) => post<DTO<"ValueRequestView">>('/projects/' + id + '/outcome-requests', data),
getDemandPoolOutcomeContext: (token: string) => get<DTO<"OutcomeContext">>('/demand-pool-outcome-context?token=' + encodeURIComponent(token)),
submitDemandPoolOutcome: (data: DTO<"OutcomeSubmission">) => post<DTO<"OutcomeResult">>('/demand-pool-outcome-submit', data),
sendDemandPoolOutcomeRequest: (id: string) => post<DTO<"ValueRequestView">>('/demand-pool-value-requests/' + id + '/send', {}),
markDemandPoolOutcomeViewed: (id: string) => post<DTO<"ValueRequestView">>('/demand-pool-value-requests/' + id + '/view', {})
}
