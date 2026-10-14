import { get,post,put,del } from "./stage2-transport"
import type { DTO } from "./compat"
export const notificationsClient={
// Notifications
getNotificationTargets: () => get<DTO<"NotificationView">[]>('/notification/targets'),
getNotificationDeliveries: (limit = 50) => get<DTO<"DeliveryLog">[]>('/notification/deliveries?limit=' + encodeURIComponent(String(limit))),
createNotificationTarget: (data: DTO<"NotificationWrite">) => post<DTO<"NotificationView">>('/notification/targets', data),
updateNotificationTarget: (id: string, data: DTO<"NotificationWrite">) => put<DTO<"NotificationView">>('/notification/targets/' + id, data),
deleteNotificationTarget: (id: string) => del<DTO<"Ok">>('/notification/targets/' + id),
getNotificationPreview: (data: DTO<"NotificationWrite">) => post<DTO<"NotificationResult">>('/notification/preview', data),
syncNotification: (data: DTO<"NotificationSync">) => post<DTO<"NotificationResult">>('/notification/sync', data)
}
