<script lang="ts" setup>
import { computed, provide, onBeforeMount, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin6'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { usePerms } from '@/composables/usePerms.ts'
import { type DownPay } from '@/store/types/payment'
import type { Project } from '@/store/types/project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import DownPayAddForm from '@/views/projects/DownPay/components/DownPayAddForm.vue'
import DownPayFormList from '@/views/projects/DownPay/components/DownPayFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)

const contStore = useContract()
const orderGroupList = computed(() => contStore.orderGroupList)
provide('orders', orderGroupList)

const pDataStore = useProjectData()
const unitTypeList = computed(() => pDataStore.unitTypeList)
provide('types', unitTypeList)

const payStore = usePayment()

const fetchOrderGroupList = (projId: number) => contStore.fetchOrderGroupList(projId)
const fetchTypeList = (projId: number) => pDataStore.fetchTypeList(projId)
const fetchDownPayList = (payload: { project: number; order_group?: number; unit_type?: number }) =>
  payStore.fetchDownPayList(payload)
const createDownPay = (payload: DownPay) => payStore.createDownPay(payload)
const updateDownPay = (payload: DownPay) => payStore.updateDownPay(payload)
const deleteDownPay = (pk: number, projId: number) => payStore.deleteDownPay(pk, projId)

const onCreateDownPay = (payload: {
  order_group: number
  unit_type: number
  payment_amount: number
}) => {
  if (project.value) {
    createDownPay({
      project: project.value,
      order_group: payload.order_group,
      unit_type: payload.unit_type,
      payment_amount: payload.payment_amount,
    })
  }
}

const onUpdateDownPay = (payload: DownPay) => {
  if (project.value) {
    updateDownPay({
      ...payload,
      project: project.value,
    })
  }
}

const onDeleteDownPay = (pk: number) => {
  if (project.value) deleteDownPay(pk, project.value)
}

const dataSetup = async (pk: number) => {
  await Promise.all([fetchOrderGroupList(pk), fetchTypeList(pk), fetchDownPayList({ project: pk })])
}

const dataReset = () => {
  contStore.orderGroupList = []
  pDataStore.unitTypeList = []
  payStore.downPayList = []
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
        <DownPayAddForm v-if="canProjectUpdate" :disabled="!project" @on-submit="onCreateDownPay" />
        <DownPayFormList @on-update="onUpdateDownPay" @on-delete="onDeleteDownPay" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
