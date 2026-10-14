import { get, post, put, del, postMultipart, postDetailed, lifecycleCall, getBlob, download } from "./stage2-transport"
import type { DTO } from "./compat"
export const deliveryClient = {
getRequirementLifecycle: (id: string) => lifecycleCall<DTO<"LifecycleView">>('/requirements/' + id + '/lifecycle'),
getDeliveryBaselines: (id: string) => lifecycleCall<DTO<"BaselinesView">>('/requirements/' + id + '/delivery-baselines'),
createDeliveryBaseline: (id: string, data: DTO<"DeliveryBaselineWrite">) => lifecycleCall<DTO<"BaselineRow">>('/requirements/' + id + '/delivery-baselines', 'POST', data),
createCollaborationLink: (id: string, data: DTO<"CollaborationLinkWrite">) => lifecycleCall<DTO<"LinkView">>('/requirements/' + id + '/collaboration-links', 'POST', data),
revokeCollaborationLink: (id: string) => lifecycleCall<DTO<"ApiOk">>('/collaboration-links/' + id + '/revoke', 'POST'),
deliverRequirement: (id: string, data: DTO<"DeliveryWrite">) => lifecycleCall<DTO<"PostlaunchView">>('/requirements/' + id + '/deliveries', 'POST', data),
routeDeliveryFeedback: (id: string, routeType: string) => lifecycleCall<DTO<"FeedbackRow">>('/delivery-feedback/' + id + '/route', 'POST', { routeType }),
getCollaborationLinkContext: (token: string) => lifecycleCall<DTO<"LinkView">>('/collaboration-link/context', 'GET', undefined, token),
submitCollaborationLink: (token: string, data: DTO<"CollaborationSubmission">) => lifecycleCall<DTO<"LinkView">>('/collaboration-link/submit', 'POST', data, token),
uploadCollaborationLinkFile: (token: string, file: File, key: string) => {
    const data = new FormData();
    data.append('file', file);
    data.append('uploadKey', key);
    return lifecycleCall<DTO<"AttachmentView">>('/collaboration-link/attachments', 'POST', data, token);
},
downloadCollaborationLinkFile: (token: string, id: string) => download("/collaboration-link/attachments/" + id, token)
}
