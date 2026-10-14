import { api as phase2 } from "./demand-delivery-api"
import { pocClient } from "./poc-client"
import { insightsClient } from "./insights-client"
import { notificationsClient } from "./notifications-client"
import { systemClient } from "./system-client"
export const api={...phase2,...pocClient,...insightsClient,...notificationsClient,...systemClient}
