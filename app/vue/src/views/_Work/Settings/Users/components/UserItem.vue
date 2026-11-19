<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { timeFormat, elapsedTime } from '@/utils/baseMixins'
import { useAccount } from '@/store/pinia/account'
import type { User } from '@/store/types/accounts'

const props = defineProps({
  user: { type: Object as PropType<User>, required: true },
})

const router = useRouter()
const accStore = useAccount()

const canEditUser = computed(() => {
  if (!accStore.workManager) return false
  if (props.user.pk === accStore.userInfo?.pk) return false
  if (props.user.is_superuser && !accStore.superAuth) return false
  return true
})

const adminRoleLabel = computed(() => {
  if (props.user.is_superuser) return '최고관리자'
  if (props.user.work_manager) return '업무관리자'
  return '-'
})
</script>

<template>
  <CTableRow :class="{ 'text-muted': !user.is_active }">
    <CTableDataCell>
      <router-link :to="{ name: '사용자 - 보기', params: { userId: user.pk } }">
        {{ user.username }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ user.profile?.name }}</CTableDataCell>
    <CTableDataCell>{{ user.email }}</CTableDataCell>
    <CTableDataCell>
      <v-chip size="x-small" :color="user.is_active ? 'success' : 'grey'" variant="tonal">
        {{ user.is_active ? '활성' : '비활성' }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell>{{ adminRoleLabel }}</CTableDataCell>
    <CTableDataCell>{{ timeFormat(user.date_joined) }}</CTableDataCell>
    <CTableDataCell>{{ elapsedTime(user.last_login as string) }}</CTableDataCell>
    <CTableDataCell class="py-0 text-end">
      <CDropdown
        v-if="canEditUser"
        color="secondary"
        variant="input-group"
        placement="bottom-end"
      >
        <CDropdownToggle
          :caret="false"
          color="light"
          variant="ghost"
          size="sm"
          shape="rounded-pill"
        >
          <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
          <v-tooltip activator="parent" location="top">Actions</v-tooltip>
        </CDropdownToggle>
        <CDropdownMenu>
          <CDropdownItem
            @click="router.push({ name: '사용자 - 수정', params: { userId: user.pk } })"
          >
            <span>
              <v-icon icon="mdi-pencil" color="yellow-darken-2" size="small" class="me-1" />
              편집
            </span>
          </CDropdownItem>
        </CDropdownMenu>
      </CDropdown>
    </CTableDataCell>
  </CTableRow>
</template>
