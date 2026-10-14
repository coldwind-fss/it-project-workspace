import { get, post, put, del, postMultipart, postDetailed, lifecycleCall, getBlob, download } from "./stage2-transport"
import type { DTO } from "./compat"
export const demandClient = {
getDemandPoolOptions: () => get<DTO<"DemandOptions">>('/demand-pool/options'),
getDemandPool: (params?: {
    status?: string;
    department?: string;
}) => {
    const p: string[] = [];
    if (params?.status)
        p.push('status=' + encodeURIComponent(params.status));
    if (params?.department)
        p.push('department=' + encodeURIComponent(params.department));
    return get<DTO<"DemandView">[]>('/demand-pool' + (p.length ? '?' + p.join('&') : ''));
},
getDemandPoolItem: (id: string) => get<DTO<"DemandView">>('/demand-pool/' + id),
createDemandPoolItem: (data: DTO<"DemandCreate">) => post<DTO<"DemandView">>('/demand-pool', data),
updateDemandPoolItem: (id: string, data: DTO<"DemandEvaluation">) => put<DTO<"DemandView">>('/demand-pool/' + id, data),
saveDemandPoolDecomposition: (id: string, data: DTO<"DemandDecomposition">) => put<DTO<"DecompositionView">>('/demand-pool/' + id + '/decomposition', data),
historicalDecomposeDemandPool: (id: string, data: DTO<"DemandDecomposition">) => postDetailed<DTO<"ConversionView">>('/demand-pool/' + id + '/historical-decomposition', data),
saveDemandPoolBranchDecisions: (id: string, data: DTO<"BranchDecisions">) => put<DTO<"DemandResult">>('/demand-pool/' + id + '/branch-decisions', data),
deleteDemandPoolItem: (id: string) => del<DTO<"ApiOk">>('/demand-pool/' + id),
createDemandPoolConfirmation: (id: string, data?: DTO<"ConfirmationCreate">) => post<DTO<"ConfirmationView">>('/demand-pool/' + id + '/confirmations', data || {}),
resendDemandPoolConfirmation: (id: string) => postDetailed<DTO<"ConfirmationView">>('/demand-pool/' + id + '/confirmations/resend', {}),
getDemandPoolConfirmation: (id: string) => get<DTO<"ConfirmationView">>('/demand-pool-confirmations/' + id),
submitDemandPoolConfirmation: (id: string, data: DTO<"ConfirmationSubmission">) => post<DTO<"ConfirmationView">>('/demand-pool-confirmations/' + id, data),
getDemandPoolConfirmationByToken: (token: string) => get<DTO<"ConfirmationView">>('/demand-pool-confirmations/by-token?token=' + encodeURIComponent(token)),
submitDemandPoolConfirmationByToken: (token: string, data: DTO<"ConfirmationSubmission">) => post<DTO<"ConfirmationView">>('/demand-pool-confirmations/by-token', { ...data, token }),
convertDemandPool: (id: string, data: DTO<"DemandConversion">) => postDetailed<DTO<"ConversionView">>('/demand-pool/' + id + '/convert', data),
getDemandPoolNotifications: () => get<DTO<"CollectionNotificationView">[]>('/demand-pool/notifications'),
updateDemandPoolNotification: (id: string, data: DTO<"CollectionSchedule">) => put<DTO<"CollectionNotificationView">>('/demand-pool/notifications/' + id, data),
getDemandPoolEntryContext: (token: string) => get<DTO<"EntryContext">>('/demand-pool/entry-context?token=' + encodeURIComponent(token)),
sendDemandPoolNotification: (data: DTO<"CollectionNotification">) => post<DTO<"CollectionNotificationView">>('/demand-pool/notifications', data),
submitDemandCollectionResponse: (data: DTO<"CollectionResponse">) => post<DTO<"CollectionResponseView">>('/demand-collections/responses', data),
getDemandCollectionBatches: () => get<DTO<"CollectionBatchView">[]>('/demand-collections/batches'),
getDemandCollectionBatch: (id: string) => get<DTO<"CollectionBatchView">>('/demand-collections/batches/' + id),
retryDemandCollectionFailures: (id: string) => post<DTO<"RetryCollectionView">>('/demand-collections/batches/' + id + '/retry-failures', {}),
getDemandCollectionResponse: (id: string) => get<DTO<"CollectionResponseView">>('/demand-collections/responses/' + id),
judgeDemandCollectionResponse: (id: string, data: DTO<"CollectionJudgment">) => put<DTO<"CollectionResponseView">>('/demand-collections/responses/' + id, data),
submitDemandPoolMaterials: (data: DTO<"MaterialsSubmission">) => post<DTO<"SupplementRow">>('/demand-pool/materials', data),
assignDemandPoolReviews: (id: string, data: DTO<"ReviewAssignment">) => post<DTO<"ReviewAssignmentView">>('/demand-pool/' + id + '/reviews', data),
reuseDemandPoolBusinessReview: (id: string, data: DTO<"ReviewReuse">) => postDetailed<DTO<"ReviewAssignmentView">>('/demand-pool/' + id + '/reviews/reuse', data),
getDemandPoolReview: (id: string) => get<DTO<"ReviewView">>('/demand-pool-reviews/' + id),
submitDemandPoolReview: (id: string, data: DTO<"ReviewSubmission">) => post<DTO<"ReviewView">>('/demand-pool-reviews/' + id, data),
getDemandPoolReviewByToken: (token: string) => get<DTO<"ReviewView">>('/demand-pool-reviews/by-token?token=' + encodeURIComponent(token)),
submitDemandPoolReviewByToken: (token: string, data: DTO<"ReviewSubmission">) => post<DTO<"ReviewView">>('/demand-pool-reviews/by-token', { ...data, token }),
getDemandPoolSupplements: (id: string) => get<DTO<"SupplementRow">[]>('/demand-pool/' + id + '/supplements'),
getDemandPoolSupplement: (id: string) => get<DTO<"SupplementRow">>('/demand-pool-supplements/' + id),
createDemandPoolSupplement: (id: string, data: DTO<"SupplementCreate">) => post<DTO<"SupplementRow">>('/demand-pool/' + id + '/supplements', data),
submitDemandPoolSupplement: (id: string, data: DTO<"SupplementSubmission">) => put<DTO<"SupplementRow">>('/demand-pool-supplements/' + id, data),
getDemandPoolPocs: (id: string) => get<DTO<"PoolPocRow">[]>('/demand-pool/' + id + '/pocs'),
createDemandPoolPoc: (id: string, data: DTO<"PoolPocCreate">) => post<DTO<"PoolPocRow">>('/demand-pool/' + id + '/pocs', data),
updateDemandPoolPoc: (id: string, data: DTO<"PoolPocUpdate">) => put<DTO<"PoolPocRow">>('/demand-pool-pocs/' + id, data),
getDemandPoolValueCard: (id: string) => get<DTO<"ValueCardView">>('/demand-pool/' + id + '/value-card'),
saveDemandPoolValueCard: (id: string, data: DTO<"ValueCardWrite">) => put<DTO<"ValueCardView">>('/demand-pool/' + id + '/value-card', data),
getDemandPoolOutcomeRequests: (id: string) => get<DTO<"ValueRequestView">[]>('/demand-pool/' + id + '/outcome-requests'),
createDemandPoolOutcomeRequest: (id: string, data: DTO<"OutcomeRequestWrite">) => post<DTO<"ValueRequestView">>('/demand-pool/' + id + '/outcome-requests', data),
getDemandPoolOutcomeContext: (token: string) => get<DTO<"OutcomeContext">>('/demand-pool-outcome-context?token=' + encodeURIComponent(token)),
submitDemandPoolOutcome: (data: DTO<"OutcomeSubmission">) => post<DTO<"OutcomeResult">>('/demand-pool-outcome-submit', data),
sendDemandPoolOutcomeRequest: (id: string) => post<DTO<"ValueRequestView">>('/demand-pool-value-requests/' + id + '/send', {}),
markDemandPoolOutcomeViewed: (id: string) => post<DTO<"ValueRequestView">>('/demand-pool-value-requests/' + id + '/view', {})
}
