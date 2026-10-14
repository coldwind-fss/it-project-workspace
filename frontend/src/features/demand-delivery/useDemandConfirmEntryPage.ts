
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
import { deliveryStandardFields } from '../../shared/deliveryStandards'
export function useDemandConfirmEntryPage() {


const route = useRoute()
const confirmationId = String(route.query.confirmationId || '').trim()
const confirmationToken = String(route.query.token || '').trim()
const confirmation = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const successDetail = ref('')
const form = ref<any>({ decision: 'confirmed', confirmationComment: '' })
const content = computed(() => confirmation.value?.content || {})
const valueDefinition = computed(() => content.value?.valueDefinition && typeof content.value.valueDefinition === 'object' ? content.value.valueDefinition : {})
const templateFields = computed(() => deliveryStandardFields(confirmation.value?.templateType || confirmation.value?.demand?.solutionType || 'custom'))
const populatedTemplateFields = computed(() => templateFields.value.filter(field => String(content.value?.[field.key] || '').trim()))
const verificationModeLabel = computed(() => valueDefinition.value.verificationMode === 'quantitative' ? '量化前后对比' : valueDefinition.value.verificationMode === 'outcome' ? '结果 / 定性验证' : '历史数据')
const canSubmit = computed(() => !!confirmation.value && confirmation.value.status === 'pending' && ['confirmed', 'changes_requested'].includes(form.value.decision) && (form.value.decision !== 'changes_requested' || !!form.value.confirmationComment?.trim()))

async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  errorMessage.value = ''
  const payload = { decision: form.value.decision, confirmationComment: form.value.confirmationComment }
  const result: any = confirmationToken ? await api.submitDemandPoolConfirmationByToken(confirmationToken, payload) : await api.submitDemandPoolConfirmation(confirmationId, payload)
  saving.value = false
  if (!result?.id) { errorMessage.value = result?.error || '确认提交失败，请重试。'; return }
  const approved = form.value.decision === 'confirmed'
  successMessage.value = approved ? '交付与价值口径已确认' : '已退回给 IT 修改'
  successDetail.value = approved ? '确认内容已经回写需求池，IT 可以据此继续正式立项。' : '你的修改意见已回写需求池，IT 调整后会重新发送确认。'
  confirmation.value = result
}

onMounted(async () => {
  if (!confirmationToken && !confirmationId) { errorMessage.value = '确认单链接无效。'; loading.value = false; return }
  const result: any = confirmationToken ? await api.getDemandPoolConfirmationByToken(confirmationToken) : await api.getDemandPoolConfirmation(confirmationId)
  if (result) confirmation.value = result
  else errorMessage.value = '确认单读取失败，请重试。'
  loading.value = false
})
return { route, confirmationId, confirmationToken, confirmation, loading, saving, errorMessage, successMessage, successDetail, form, content, valueDefinition, templateFields, populatedTemplateFields, verificationModeLabel, canSubmit, submit }
}
