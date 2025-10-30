<script lang="ts" setup>
import { computed, provide, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin6'
import { write_project } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { type DownPay } from '@/store/types/payment'
import type { Project } from '@/store/types/project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import DownPayAddForm from '@/views/projects/DownPay/components/DownPayAddForm.vue'
import DownPayFormList from '@/views/projects/DownPay/components/DownPayFormList.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const contStore = useContract()
const orderGroupList = computed(() => contStore.orderGroupList)
provide('orders', orderGroupList)

const pDataStore = useProjectData()
const unitTypeList = computed(() => pDataStore.unitTypeList)
provide('types', unitTypeList)

const fetchOrderGroupList = (projId: number) => contStore.fetchOrderGroupList(projId)

const fetchTypeList = (projId: number) => pDataStore.fetchTypeList(projId)

const payStore = usePayment()
const fetchDownPayList = (payload: { project: number; order_group?: number; unit_type?: number }) =>
  payStore.fetchDownPayList(payload)
const createDownPay = (payload: DownPay) => payStore.createDownPay(payload)
const updateDownPay = (payload: DownPay) => payStore.updateDownPay(payload)
const deleteDownPay = (pk: number, projId: number) => payStore.deleteDownPay(pk, projId)

const onCreateDownPay = (payload: DownPay) =>
  createDownPay({ ...{ project: project.value }, ...payload })

const onUpdateDownPay = (payload: DownPay) =>
  updateDownPay({ ...{ project: project.value }, ...payload })

const onDeleteDownPay = (pk: number) => {
  if (project.value) deleteDownPay(pk, project.value)
}

const dataSetup = (pk: number) => {
  fetchOrderGroupList(pk)
  fetchTypeList(pk)
  fetchDownPayList({ project: pk })
}

const dataReset = () => {
  contStore.orderGroupList = []
  pDataStore.unitTypeList = []
  payStore.downPayList = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(project.value || projStore.initProjId)
  loading.value = false
})
</script>
<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <DownPayAddForm v-if="write_project" :disabled="!project" @on-submit="onCreateDownPay" />
        <DownPayFormList @on-update="onUpdateDownPay" @on-delete="onDeleteDownPay" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
