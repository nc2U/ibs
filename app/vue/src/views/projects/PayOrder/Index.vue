<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin6'
import { useProject } from '@/store/pinia/project'
import { usePayment } from '@/store/pinia/payment'
import { usePerms } from '@/composables/usePerms'
import type { PayOrder } from '@/store/types/payment'
import type { Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import PayOrderAddForm from '@/views/projects/PayOrder/components/PayOrderAddForm.vue'
import PayOrderFormList from '@/views/projects/PayOrder/components/PayOrderFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const payStore = usePayment()
const fetchPayOrderList = (projId: number) => payStore.fetchPayOrderList(projId)
const createPayOrder = (payload: PayOrder) => payStore.createPayOrder(payload)
const updatePayOrder = (payload: PayOrder) => payStore.updatePayOrder(payload)
const deletePayOrder = (pk: number, projId: number) => payStore.deletePayOrder(pk, projId)

const onSubmit = (payload: Omit<PayOrder, 'pk' | 'project'>) => {
  if (project.value) createPayOrder({ project: project.value, ...payload })
}

const onUpdatePayOrder = (payload: PayOrder) => {
  if (project.value) updatePayOrder({ ...payload, project: project.value })
}

const onDeletePayOrder = (pk: number) => {
  if (project.value) deletePayOrder(pk, project.value)
}

const dataReset = () => {
  payStore.payOrderList = []
}

const dataSetup = async (pk: number) => {
  await fetchPayOrderList(pk)
}

watch(
  () => project.value,
  newProjId => {
    dataReset()
    if (newProjId) dataSetup(newProjId)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) await dataSetup(project.value)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <PayOrderAddForm v-if="canProjectUpdate" :disabled="!project" @on-submit="onSubmit" />
        <PayOrderFormList @on-update="onUpdatePayOrder" @on-delete="onDeletePayOrder" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
