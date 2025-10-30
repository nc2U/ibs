<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin6'
import { write_project } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { usePayment } from '@/store/pinia/payment'
import { type PayOrder } from '@/store/types/payment'
import type { Project } from '@/store/types/project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import PayOrderAddForm from '@/views/projects/PayOrder/components/PayOrderAddForm.vue'
import PayOrderFormList from '@/views/projects/PayOrder/components/PayOrderFormList.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const payStore = usePayment()
const fetchPayOrderList = (projId: number) => payStore.fetchPayOrderList(projId)
const createPayOrder = (payload: PayOrder) => payStore.createPayOrder(payload)
const updatePayOrder = (payload: PayOrder) => payStore.updatePayOrder(payload)
const deletePayOrder = (pk: number, projId: number) => payStore.deletePayOrder(pk, projId)

const onSubmit = (payload: PayOrder) =>
  createPayOrder({ ...{ project: project.value as number }, ...payload })

const onUpdatePayOrder = (payload: PayOrder) =>
  updatePayOrder({ ...{ project: project.value as number }, ...payload })

const onDeletePayOrder = (pk: number) => {
  if (project.value) deletePayOrder(pk, project.value)
}

const projSelect = (target: number | null) => {
  payStore.payOrderList = []
  if (!!target) fetchPayOrderList(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await fetchPayOrderList(project.value || projStore.initProjId)
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
        <PayOrderAddForm v-if="write_project" :disabled="!project" @on-submit="onSubmit" />
        <PayOrderFormList @on-update="onUpdatePayOrder" @on-delete="onDeletePayOrder" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
