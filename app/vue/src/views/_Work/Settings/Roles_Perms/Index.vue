<script setup lang="ts">
import { onBeforeMount, ref, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin3'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { storeToRefs } from 'pinia'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import RoleList from './components/RoleList.vue'
import PermissionReport from './components/PermissionReport.vue'
import RoleFormModal from './components/RoleFormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import type { Role } from '@/store/types/work_project'
import { useAccount } from '@/store/pinia/account.ts'

const route = useRoute()

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)

const workStore = useWork()
const { roleList, permissionList } = storeToRefs(workStore)

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const activeTab = ref(0)
const loading = ref(true)

const refConfirmModal = ref()
const pkToDelete = ref<number | null>(null)

const roleModal = ref(false)
const selectedRole = ref<Role | null>(null)
const maxOrder = computed(() =>
  roleList.value.length ? Math.max(...roleList.value.map(r => r.order)) : 0,
)

const showRoleModal = (role: Role | null = null) => {
  selectedRole.value = role
  roleModal.value = true
}

const deleteRole = (pk: number) => {
  pkToDelete.value = pk
  refConfirmModal.value.callModal(
    '역할 삭제',
    '이 작업은 되돌릴 수 없습니다. 정말로 이 역할을 삭제하시겠습니까?',
    'mdi-trash-can-outline',
    'danger',
  )
}

const roleDelete = async () => {
  if (pkToDelete.value) {
    await workStore.deleteRole(pkToDelete.value)
    refConfirmModal.value.close()
  }
}

onBeforeMount(async () => {
  await workStore.fetchRoleList()
  await workStore.fetchPermissionList()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="pageTitle" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <CNav variant="tabs" class="mb-3">
            <CNavItem>
              <CNavLink href="javascript:void(0)" :active="activeTab === 0" @click="activeTab = 0">
                역할
              </CNavLink>
            </CNavItem>
            <CNavItem>
              <CNavLink href="javascript:void(0)" :active="activeTab === 1" @click="activeTab = 1">
                권한 보고서
              </CNavLink>
            </CNavItem>
          </CNav>

          <div v-if="activeTab === 0">
            <RoleList
              :role-list="roleList"
              :work-manager="!!workManager"
              @show-modal="showRoleModal"
              @delete-role="deleteRole"
            />
          </div>

          <div v-else-if="activeTab === 1">
            <PermissionReport
              :role-list="roleList"
              :work-manager="!!workManager"
              :permission-list="permissionList"
            />
          </div>
        </CCol>
      </CRow>

      <RoleFormModal
        :visible="roleModal"
        :role="selectedRole"
        :max-order="maxOrder"
        :work-manager="!!workManager"
        @close="roleModal = false"
      />

      <ConfirmModal ref="refConfirmModal">
        <template #footer>
          <v-btn color="warning" size="small" @click="roleDelete">삭제</v-btn>
        </template>
      </ConfirmModal>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
