import { api as phase1 } from "./core-api"
import { collaborationClient } from "./collaboration-client"
import { demandClient } from "./demand-client"
import { deliveryClient } from "./delivery-client"
import { postlaunchClient } from "./postlaunch-client"
import { valueClient } from "./value-client"
export const api = { ...phase1, ...collaborationClient, ...demandClient, ...deliveryClient, ...postlaunchClient, ...valueClient }
