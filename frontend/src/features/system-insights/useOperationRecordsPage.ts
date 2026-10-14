
import { onMounted, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { api } from '../../api/application-api'
export function useOperationRecordsPage(){


const rows = ref<any[]>([])
const filters = ref({ entityType: '', action: '', keyword: '' })

function actionText(action: string) {
  return { create: '新增', update: '修改', delete: '删除' }[action] || action
}
function actionClass(action: string) {
  return {
    create: 'bg-green-50 text-green-600',
    update: 'bg-blue-50 text-blue-600',
    delete: 'bg-red-50 text-red-600',
  }[action] || 'bg-gray-100 text-gray-600'
}
async function loadData() {
  const data = await api.getOperations(filters.value)
  if (data) rows.value = data
}

onMounted(loadData)
return { rows, filters, actionText, actionClass, loadData }
}
