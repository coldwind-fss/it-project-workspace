import { get,post,put,del } from "./stage2-transport"
import type { DTO } from "./compat"
export const systemClient={
getRecycleBin: () => get<DTO<"RecycleRow">[]>('/recycle-bin'),
restoreRecycleItem: (type: string, id: string) => post<DTO<"Ok">>(`/recycle-bin/${type}/${id}/restore`, {}),
purgeRecycleItem: (type: string, id: string) => del<DTO<"Ok">>(`/recycle-bin/${type}/${id}`)
}
