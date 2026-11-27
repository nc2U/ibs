<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin4'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { usePerms } from '@/composables/usePerms.ts'
import type { Project } from '@/store/types/project.ts'
import { type OrderGroup } from '@/store/types/contract'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import OrderAddForm from '@/views/projects/OrderGroup/components/OrderAddForm.vue'
import OrderFormList from '@/views/projects/OrderGroup/components/OrderFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)

const contStore = useContract()
const hasDefaultOrderGroup = computed(() =>
  contStore.orderGroupList.some(og => og.is_default_for_uncontracted),
)

const fetchOrderGroupList = (pk: number) => contStore.fetchOrderGroupList(pk)
const createOrderGroup = (payload: OrderGroup) => contStore.createOrderGroup(payload)
const updateOrderGroup = (payload: OrderGroup) => contStore.updateOrderGroup(payload)
const deleteOrderGroup = (payload: { pk: number; project: number }) =>
  contStore.deleteOrderGroup(payload)

const onSubmit = (payload: Omit<OrderGroup, 'pk' | 'project' | 'sort_desc'>) => {
  if (project.value) {
    createOrderGroup({
      project: project.value,
      ...payload,
    } as OrderGroup)
  }
}

const onUpdateOrder = (payload: OrderGroup) => {
  if (project.value) {
    updateOrderGroup({
      ...payload,
      project: project.value,
    })
  }
}

const onDeleteOrder = (pk: number) => {
  if (project.value) {
    deleteOrderGroup({ pk, project: project.value })
  }
}

watch(
  () => project.value,
  newProjId => {
    contStore.orderGroupList = []
    if (newProjId) fetchOrderGroupList(newProjId)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) await fetchOrderGroupList(project.value)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <OrderAddForm
          v-if="canProjectUpdate"
          :disabled="!project"
          :has-default="hasDefaultOrderGroup"
          @on-submit="onSubmit"
        />
        <OrderFormList @on-update="onUpdateOrder" @on-delete="onDeleteOrder" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
