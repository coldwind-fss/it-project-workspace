<template>
  <main class="h-screen min-h-screen overflow-y-auto bg-slate-50 px-4 py-5 sm:px-6 sm:py-8">
    <div class="mx-auto w-full max-w-2xl">
      <div class="mb-5 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3"><div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600 text-lg font-bold text-white shadow-sm">池</div><div><p class="text-sm font-semibold text-gray-900">需求提报</p><p class="text-[11px] text-gray-500">业务需求与新想法收集</p></div></div>
        <div class="flex flex-wrap items-center justify-end gap-2"><span class="rounded-full bg-white px-2.5 py-1 text-[10px] font-medium text-violet-600 shadow-sm">来自钉钉</span><span v-if="identityName" class="rounded-full border border-violet-100 bg-violet-50 px-2.5 py-1 text-[10px] font-medium text-violet-700">填写人：{{ identityName }}<span v-if="identityDepartment"> · {{ identityDepartment }}</span></span></div>
      </div>

      <section v-if="successMessage" class="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm sm:p-8"><div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-600">✓</div><h1 class="mt-4 text-center text-lg font-semibold text-gray-900">{{ successMessage }}</h1><p v-if="isCollection" class="mt-2 text-center text-sm leading-6 text-gray-500">已提交给 IT，等待 IT 判断是否进入需求池 · 填写人：{{ identityName || currentUser.name || '钉钉用户' }}<span v-if="submittedDemandId"> · 回执编号 {{ submittedDemandId }}</span></p><p v-else class="mt-2 text-center text-sm leading-6 text-gray-500">已保存到 IT 需求池 · 填写人：{{ identityName || currentUser.name || '钉钉用户' }}<span v-if="submittedDemandId"> · 编号 {{ submittedDemandId }}</span></p><p class="mt-1 text-center text-xs text-gray-400">{{ isCollection ? '这条内容会先进入主动征集回执，由 IT 逐条判断；有价值的内容才会转为正式需求。' : 'IT 会沿着同一条记录完成评估、确认和后续交付。' }}</p><div v-if="!isMaterials" class="mt-6 flex justify-center"><button type="button" class="feishu-btn-primary text-xs" @click="continueSubmission">继续提交需求</button></div></section>

      <section v-else class="overflow-hidden rounded-2xl border border-violet-100 bg-white shadow-sm">
        <div class="border-b border-violet-100 bg-gradient-to-r from-violet-50 via-white to-blue-50 px-5 py-5 sm:px-7"><p class="text-xs font-semibold text-violet-600">{{ isMaterials ? '需求资料补充' : isIdea ? '新想法提报' : '需求征集' }}</p><h1 class="mt-1 text-lg font-semibold text-gray-900">{{ isMaterials ? '把已沟通的需求留个记录' : isIdea ? '把刚才沟通的想法正式告诉 IT' : '把问题和期望结果告诉 IT' }}</h1><p class="mt-2 text-xs leading-5 text-gray-500">{{ isMaterials ? '不用重新填问卷，简单写几句话，或补充资料和截图即可。' : isIdea ? '按原来的需求提报方式填写即可；不确定 L2/L3 或需求类型时，由 IT 后续归类和评估。' : '想到什么写什么，不需要懂项目管理；IT 会再帮你归类和评估。' }}</p></div>
        <div class="space-y-5 px-5 py-5 sm:px-7 sm:py-6" @paste="handlePaste">
          <div v-if="errorMessage" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2.5 text-xs leading-5 text-amber-700">{{ errorMessage }}</div>
          <div v-else-if="!entryToken && !currentUser.sessionToken" class="rounded-lg border border-blue-100 bg-blue-50/70 px-3 py-2.5 text-xs leading-5 text-blue-700">当前链接未携带接收人身份。请从“IT项目协作空间”机器人收到的专属提报链接进入；专属链接会自动记录提报人，不会触发钉钉免登。</div>
          <div v-if="loading" class="py-8 text-center text-sm text-gray-400">正在准备提报表单...</div>
          <template v-else>
            <template v-if="isMaterials">
              <div v-if="entryContext?.demand" class="rounded-xl border border-amber-100 bg-amber-50/60 px-4 py-3"><p class="text-[11px] font-semibold text-amber-800">已沟通需求</p><p class="mt-1 text-sm font-semibold text-gray-900">{{ entryContext.demand.title }}</p><p class="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-600">{{ entryContext.demand.description }}</p></div>
              <label class="block"><span class="form-label">这次要做什么 / 还需要补充什么 <span class="font-normal text-gray-400">（可写几句话）</span></span><textarea v-model="materialsForm.additionalInfo" rows="6" maxlength="10000" class="feishu-input w-full resize-y text-sm leading-6" placeholder="例如：补充具体业务规则、例外情况、希望参考的页面；也可以只写‘资料见附件’" /></label>
              <AttachmentPicker :files="files" @add="addFiles" @remove="removeFile" />
              <div v-if="uploadError" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-xs leading-5 text-amber-700">{{ uploadError }}</div>
              <div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-[11px] leading-5 text-gray-400">填写人：{{ identityName || currentUser.name || '钉钉用户' }} · 文字和附件都会回写原需求。</p><button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmitMaterials" @click="submitMaterials">{{ saving ? '提交中...' : '提交补充资料' }}</button></div>
            </template>
            <template v-else-if="isIdea">
              <div class="rounded-xl border border-violet-100 bg-violet-50/60 px-4 py-3"><p class="text-xs font-semibold text-violet-800">需求提报</p><p class="mt-1 text-[11px] leading-5 text-violet-700">这是你和 IT 已经沟通过的事项，请把现有信息整理到这里；不需要自行判断需求类型。</p></div>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label class="block sm:col-span-2"><span class="form-label">需求标题 <span class="font-normal text-gray-400">（可选，不填会自动生成）</span></span><input v-model="form.title" class="feishu-input w-full" maxlength="300" placeholder="例如：订单列表需要支持批量导出" /></label>
                <label class="block sm:col-span-2"><span class="form-label">项目类型 <span class="text-rose-500">*</span></span><select v-model="form.intakeLevel" class="feishu-input w-full"><option value="L2">新项目</option><option value="L3">已有项目升级 / 迭代</option></select><span class="mt-1 block text-[10px] leading-4 text-gray-400">不确定时可以按实际理解选择，IT 会在评估阶段调整。</span></label>
                <label class="block"><span class="form-label">归属业务部门 <span class="text-rose-500">*</span></span><select v-if="departmentOptions.length" v-model="form.department" class="feishu-input w-full"><option value="">请选择部门</option><option v-for="department in departmentOptions" :key="department" :value="department">{{ department }}</option></select><input v-else v-model="form.department" class="feishu-input w-full" placeholder="例如：电商部" /></label>
                <label class="block"><span class="form-label">期望完成时间 <span class="font-normal text-gray-400">（可选）</span></span><input v-model="form.expectedDeliveryTime" type="date" class="feishu-input w-full" /></label>
                <label class="block sm:col-span-2"><span class="form-label">关联已有项目 <span class="font-normal text-gray-400">（可选）</span></span><select v-model="form.projectId" class="feishu-input w-full"><option value="">暂不确定，由 IT 归类</option><option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option></select></label>
                <label class="block sm:col-span-2"><span class="form-label">当前问题与期望结果 <span class="text-rose-500">*</span></span><textarea v-model="form.description" rows="7" maxlength="10000" class="feishu-input w-full resize-y text-sm leading-6" placeholder="请描述现在遇到的问题，以及希望最终达到的结果；可以直接粘贴截图" /></label>
              </div>
              <AttachmentPicker :files="files" @add="addFiles" @remove="removeFile" />
              <div v-if="uploadError" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-xs leading-5 text-amber-700">{{ uploadError }}</div>
              <div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-[11px] leading-5 text-gray-400">填写人：{{ identityName || currentUser.name || '钉钉用户' }} · 提交后进入需求池待 IT 评估。</p><button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmit" @click="submit">{{ saving ? '提交中...' : '提交需求提报' }}</button></div>
            </template>
            <template v-else>
            <div class="rounded-xl border border-violet-100 bg-violet-50/60 px-4 py-3"><p class="text-xs font-semibold text-violet-800">先从最贴近的情况开始</p><p class="mt-1 text-[11px] leading-5 text-violet-700">不用想项目名称，也不用判断 L2/L3，选一个最像的，再说说哪里不方便。</p><div class="mt-3 flex flex-wrap gap-2"><button v-for="item in collectionTopics" :key="item.key" type="button" :class="['rounded-full border px-3 py-1.5 text-xs transition-colors', collectionForm.topic === item.key ? 'border-violet-500 bg-violet-600 text-white' : 'border-violet-200 bg-white text-violet-700 hover:border-violet-400']" @click="collectionForm.topic = item.key">{{ item.label }}</button></div></div>
            <label class="block"><span class="form-label">哪里不方便？ <span class="text-rose-500">*</span></span><textarea v-model="collectionForm.problem" rows="5" maxlength="10000" class="feishu-input w-full resize-y text-sm leading-6" placeholder="例如：每周都要把多个 Excel 合并，再逐条核对，容易漏数据。想到什么写什么即可。" /></label>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2"><label class="block"><span class="form-label">大概多久遇到一次？ <span class="font-normal text-gray-400">（可选）</span></span><select v-model="collectionForm.frequency" class="feishu-input w-full"><option value="">不确定</option><option value="每天">每天</option><option value="每周">每周</option><option value="每月">每月</option><option value="偶尔">偶尔</option></select></label><label class="block"><span class="form-label">归属部门</span><input v-model="form.department" class="feishu-input w-full" :readonly="!!identityDepartment" :placeholder="identityDepartment || '例如：电商部'" /></label></div>
            <label class="block"><span class="form-label">希望以后怎样？ <span class="font-normal text-gray-400">（可选）</span></span><textarea v-model="collectionForm.desired" rows="3" maxlength="5000" class="feishu-input w-full resize-y" placeholder="例如：自动汇总，少填表，查询更快；暂时想不到也可以不填。" /></label>
            <AttachmentPicker :files="files" @add="addFiles" @remove="removeFile" />
            <div v-if="uploadError" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-xs leading-5 text-amber-700">{{ uploadError }}</div>
            <div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-[11px] leading-5 text-gray-400">填写人：{{ identityName || currentUser.name || '钉钉用户' }} · IT 会根据内容完成归类和评估。</p><button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmitCollection" @click="submitCollection">{{ saving ? '提交中...' : '提交需求想法' }}</button></div>
            </template>
          </template>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import AttachmentPicker from '../components/AttachmentPicker.vue'
import { useDemandEntryPage } from "../features/demand-delivery/useDemandEntryPage"
const { currentUser, projects, departmentOptions, files, loading, saving, errorMessage, uploadError, successMessage, submittedDemandId, entryToken, entryContext, entryMode, form, materialsForm, collectionTopics, collectionForm, identityName, identityDepartment, canSubmit, isMaterials, canSubmitMaterials, canSubmitCollection, isIdea, isCollection, readUser, readEntryToken, readEntryMode, withTimeout, waitForDingTalkSdk, ensureAuth, addFiles, removeFile, handlePaste, submit, submitCollection, submitMaterials, continueSubmission } = useDemandEntryPage()
</script>

<style scoped>
.form-label { display: block; margin-bottom: 0.35rem; font-size: 0.7rem; color: #6b7280; }
</style>
