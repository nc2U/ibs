<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/settings/_menu/headermixin'
import type { User } from '@/store/types/accounts'
import { useAccount } from '@/store/pinia/account'
import { bgLight } from '@/utils/cssMixins'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import SettingsAuthGuard from '@/components/AuthGuard/SettingsAuthGuard.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import UserSelect from './components/UserSelect.vue'
import SideBarManageAuth from './components/SideBarManageAuth.vue'
import AddUserFormModal from './components/AddUserFormModal.vue'

const refFormModal = ref<InstanceType<typeof AddUserFormModal> | null>(null)
const refStatusConfirm = ref<InstanceType<typeof ConfirmModal> | null>(null)

const accStore = useAccount()
const user = computed<User | null>(() => accStore.user)
const workManager = computed(() => Boolean(accStore.workManager))
const superAuth = computed(() => Boolean(accStore.superAuth))
const isSelf = computed(() => Boolean(user.value?.pk && user.value.pk === accStore.userInfo?.pk))
const canEditTargetAccount = computed(() => {
  if (!user.value?.pk || !workManager.value) return false
  if (user.value.is_superuser && !superAuth.value) return false
  return true
})

const selectUser = async (pk: number | null) => {
  if (pk) {
    await accStore.fetchUser(pk, { is_active: 'all' })
  } else {
    accStore.removeUser()
  }
}

const onUserCreated = async (pk: number) => {
  await accStore.fetchUsersList('all')
  await selectUser(pk)
}

type PendingAccountAction = {
  field: 'is_active' | 'work_manager' | 'is_staff'
  value: boolean
  title: string
  body: string
}
const pendingAction = ref<PendingAccountAction | null>(null)
const isUpdatingStatus = ref(false)

const requestAccountToggle = (field: 'is_active' | 'work_manager' | 'is_staff') => {
  if (!user.value || !canEditTargetAccount.value || isUpdatingStatus.value) return
  if (field === 'is_staff' && (!superAuth.value || isSelf.value)) return
  if (field === 'is_active' && isSelf.value) return
  if (field === 'work_manager' && isSelf.value && !superAuth.value) return

  const nextVal = !user.value[field]
  const labelMap = {
    is_active: nextVal ? '계정 활성화(가입 승인)' : '계정 비활성화',
    work_manager: nextVal ? '업무관리자 권한 부여' : '업무관리자 권한 해제',
    is_staff: nextVal ? '스태프 권한 부여' : '스태프 권한 해제',
  }
  pendingAction.value = {
    field,
    value: nextVal,
    title: '계정 권한 상태 변경',
    body: `[${user.value.username}] 사용자의 ${labelMap[field]}을(를) 진행하시겠습니까?`,
  }
  refStatusConfirm.value?.callModal(
    pendingAction.value.title,
    pendingAction.value.body,
    'mdi-account-cog',
    nextVal ? 'primary' : 'warning',
    '변경',
    nextVal ? 'primary' : 'warning',
  )
}

const executeAccountToggle = async () => {
  if (!user.value?.pk || !pendingAction.value || isUpdatingStatus.value) return
  const { field, value } = pendingAction.value
  isUpdatingStatus.value = true
  try {
    const updated = await accStore.adminUpdateUser({
      email: user.value.email,
      [field]: value,
    })
    if (updated) {
      const nextUserInfo =
        isSelf.value && accStore.userInfo ? { ...accStore.userInfo, [field]: value } : null
      refStatusConfirm.value?.close()
      pendingAction.value = null
      await selectUser(user.value.pk)
      if (nextUserInfo) {
        accStore.userInfo = nextUserInfo
      }
    }
  } finally {
    isUpdatingStatus.value = false
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  await accStore.fetchUsersList('all')
  if (accStore?.userInfo?.pk) await selectUser(accStore.userInfo.pk)
  loading.value = false
})
</script>

<template>
  <SettingsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
    <ContentBody>
      <CCardBody class="p-3 p-md-4 pb-5">
        <UserSelect
          :sel-user="user?.pk ?? undefined"
          @select-user="selectUser"
          @add-user-modal="refFormModal?.callModal()"
        />

        <!-- 선택 사용자 계정 상태 / 가입 승인 -->
        <CCard v-if="user" class="mb-4">
          <CCardBody class="py-3 d-flex flex-wrap justify-content-between align-items-center gap-3" :class="bgLight">
            <div class="d-flex flex-wrap align-items-center gap-2">
              <v-icon icon="mdi-card-account-details-outline" color="primary" size="small" />
              <span class="fw-bold">{{ user.username }}</span>
              <span class="text-body-secondary small">({{ user.email }})</span>
              <span v-if="user.staff_name" class="text-body-secondary small">
                · 직원: {{ user.staff_name }}
              </span>
              <v-chip
                :color="user.is_active ? 'success' : 'warning'"
                size="x-small"
                variant="flat"
              >
                {{ user.is_active ? '활성 계정' : '승인 대기 (비활성)' }}
              </v-chip>
              <v-chip v-if="user.is_superuser" color="danger" size="x-small" variant="flat">
                최고관리자
              </v-chip>
              <v-chip v-if="user.work_manager" color="info" size="x-small" variant="flat">
                업무관리자
              </v-chip>
              <v-chip v-if="user.is_staff" color="secondary" size="x-small" variant="tonal">
                스태프
              </v-chip>
            </div>

            <div v-if="canEditTargetAccount" class="d-flex flex-wrap gap-2">
              <v-btn
                v-if="!isSelf"
                type="button"
                size="x-small"
                :color="user.is_active ? 'warning' : 'success'"
                :variant="user.is_active ? 'outlined' : 'flat'"
                :disabled="isUpdatingStatus"
                @click="requestAccountToggle('is_active')"
              >
                {{ user.is_active ? '계정 비활성화' : '가입 승인 (활성화)' }}
              </v-btn>
              <v-btn
                v-if="!(isSelf && !superAuth)"
                type="button"
                size="x-small"
                color="info"
                :variant="user.work_manager ? 'flat' : 'outlined'"
                :disabled="isUpdatingStatus"
                @click="requestAccountToggle('work_manager')"
              >
                {{ user.work_manager ? '업무관리자 해제' : '업무관리자 부여' }}
              </v-btn>
              <v-btn
                v-if="superAuth && !isSelf"
                type="button"
                size="x-small"
                color="secondary"
                :variant="user.is_staff ? 'flat' : 'outlined'"
                :disabled="isUpdatingStatus"
                @click="requestAccountToggle('is_staff')"
              >
                {{ user.is_staff ? '스태프 해제' : '스태프 부여' }}
              </v-btn>
            </div>
          </CCardBody>
          <CAlert v-if="!user.is_active" color="warning" class="mb-0 rounded-0 rounded-bottom small py-2">
            현재 승인 대기(비활성) 상태의 계정입니다. 관리자가 [가입 승인 (활성화)] 처리 후 로그인 및 시스템 이용이 가능합니다.
          </CAlert>
        </CCard>

        <SideBarManageAuth :user="user as User" />
      </CCardBody>

      <AddUserFormModal ref="refFormModal" @on-created="onUserCreated" />

      <ConfirmModal ref="refStatusConfirm">
        <template #footer>
          <v-btn
            type="button"
            size="small"
            :color="pendingAction?.value ? 'primary' : 'warning'"
            :loading="isUpdatingStatus"
            :disabled="isUpdatingStatus"
            @click="executeAccountToggle"
          >
            확인
          </v-btn>
        </template>
      </ConfirmModal>
    </ContentBody>
  </SettingsAuthGuard>
</template>
