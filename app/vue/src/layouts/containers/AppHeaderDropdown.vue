<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { useRouter } from 'vue-router'
import { type User, type Profile } from '@/store/types/accounts'
import { useAccount } from '@/store/pinia/account'
import TodoModal from '@/components/Modals/TodoModal.vue'

const props = defineProps({
  userInfo: { type: Object as PropType<User>, required: true },
  profile: { type: Object as PropType<Profile | null>, default: null },
})

const refsTodoModal = ref()

const avatarSrc = computed(() => (props.profile?.image ? props.profile?.image : ''))
const avatarText = computed(() =>
  props.userInfo ? props.userInfo.username.substring(0, 1).toUpperCase() : 'A',
)

const store = useStore()
const headerClass = computed(() => (store.theme === 'dark' ? 'bg-secondary' : 'bg-light'))

const locationBlank = (url: string) => window.open(url, '_blank')

const account = useAccount()
const itemsCount = computed(() => account.myTodos.length)

const router = useRouter()
const logout = () => {
  account.logout()
  router.push({ name: 'Login' })
}
</script>

<template>
  <CDropdown>
    <CDropdownToggle class="py-0" color="link" :caret="false">
      <CAvatar
        color="secondary"
        text-color="white"
        size="md"
        :src="avatarSrc as string"
        status="success"
      >
        {{ avatarText }}
      </CAvatar>
    </CDropdownToggle>

    <CDropdownMenu>
      <CDropdownHeader component="h6" class="fw-semibold py-2" :class="headerClass">
        {{ profile && profile.name ? profile.name : userInfo.username }}님
      </CDropdownHeader>

      <CDropdownItem @click="refsTodoModal.callModal()">
        <v-icon icon="mdi mdi-calendar-check-outline" size="small" />
        할일 관리
        <CBadge color="danger" size="sm" class="ms-auto">
          {{ itemsCount }}
        </CBadge>
      </CDropdownItem>

      <CDropdownHeader component="h6" class="fw-semibold py-2" :class="headerClass">
        Settings
      </CDropdownHeader>
      <CDropdownItem @click="router.push({ name: '마이페이지' })">
        <v-icon icon="mdi mdi-account-outline" size="small" />
        마이페이지
      </CDropdownItem>

      <CDropdownItem v-if="userInfo.is_superuser" @click="locationBlank('/admin/')">
        <v-icon icon="mdi mdi-cog-outline" size="small" />
        관리자 페이지
      </CDropdownItem>

      <CDropdownItem
        v-if="userInfo.is_superuser"
        @click="locationBlank('https://nc2u.github.io/ibs/')"
      >
        <v-icon icon="mdi mdi-file-document-outline" size="small" />
        사용자 매뉴얼
      </CDropdownItem>

      <CDropdownDivider />

      <CDropdownItem style="cursor: pointer" @click="logout">
        <v-icon icon="mdi mdi-logout-variant" size="small" />
        로그아웃
      </CDropdownItem>
    </CDropdownMenu>
  </CDropdown>

  <TodoModal ref="refsTodoModal" />
</template>
