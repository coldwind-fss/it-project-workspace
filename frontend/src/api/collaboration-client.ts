import { get, post, put, del, postMultipart, postDetailed, lifecycleCall, getBlob, download } from "./stage2-transport"
import type { DTO } from "./compat"
export const collaborationClient = {
getRequirementSharedActivities: (id: string) => get<DTO<"ActivityView">[]>('/requirements/' + id + '/shared-activities'),
createRequirementSharedActivity: (id: string, data: DTO<"SharedWrite">) => post<DTO<"ActivityView">>('/requirements/' + id + '/shared-activities', data),
getProjectSharedActivities: (id: string) => get<DTO<"ActivityView">[]>('/projects/' + id + '/shared-activities'),
createProjectSharedActivity: (id: string, data: DTO<"SharedWrite">) => post<DTO<"ActivityView">>('/projects/' + id + '/shared-activities', data),
getSharedActivityComments: (id: string) => get<DTO<"CommentView">[]>('/shared-activities/' + id + '/comments'),
createSharedActivityComment: (id: string, data: DTO<"CommentWrite">) => post<DTO<"CommentView">>('/shared-activities/' + id + '/comments', data),
getBusinessRequestOptions: () => get<DTO<"IntakeOptions">>('/business-requests/options'),
getBusinessRequests: (status?: string) => get<DTO<"IntakeView">[]>('/business-requests' + (status ? '?status=' + encodeURIComponent(status) : '')),
createBusinessRequest: (data: DTO<"IntakeWrite">) => post<DTO<"IntakeView">>('/business-requests', data),
updateBusinessRequest: (id: string, data: DTO<"IntakeWrite">) => put<DTO<"IntakeView">>('/business-requests/' + id, data),
getBusinessCollaborations: (status?: string) => get<DTO<"CollaborationView">[]>('/business-collaborations' + (status ? '?status=' + encodeURIComponent(status) : '')),
createBusinessCollaboration: (data: DTO<"ThreadWrite">) => post<DTO<"CollaborationView">>('/business-collaborations', data),
updateBusinessCollaboration: (id: string, data: DTO<"ThreadReply">) => put<DTO<"CollaborationView">>('/business-collaborations/' + id, data),
getRequirementBusinessCollaborations: (id: string) => get<DTO<"CollaborationView">[]>('/requirements/' + id + '/business-collaborations'),
createRequirementBusinessCollaboration: (id: string, data: DTO<"ThreadWrite">) => post<DTO<"CollaborationView">>('/requirements/' + id + '/business-collaborations', data),
getBusinessCollaborationMessages: (id: string) => get<DTO<"MessageView">[]>('/business-collaborations/' + id + '/messages'),
createBusinessCollaborationMessage: (id: string, data: DTO<"ThreadReply">) => post<DTO<"CollaborationView">>('/business-collaborations/' + id + '/messages', data),
uploadBusinessAttachment: (ownerType: string, ownerId: string, file: File, entryToken = '') => {
    const body = new FormData();
    body.append('ownerType', ownerType);
    body.append('ownerId', ownerId);
    if (entryToken)
        body.append('entryToken', entryToken);
    body.append('file', file, file.name);
    return postMultipart<DTO<"AttachmentView">>('/business-attachments', body);
},
getBusinessAttachmentBlob: (id: string) => getBlob('/business-attachments/' + id + '/download'),
deleteBusinessAttachment: (id: string) => del<DTO<"ApiOk">>('/business-attachments/' + id),
markTodoRead: (id: string) => put<DTO<"TodoRow">>('/todos/' + id + '/read', {}),
markTodoDone: (id: string) => put<DTO<"TodoRow">>('/todos/' + id + '/done', {})
}
