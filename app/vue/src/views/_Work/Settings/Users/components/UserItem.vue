<script lang="ts" setup>
import { type PropType } from 'vue'
import { useRouter } from 'vue-router'
import type { User } from '@/store/types/accounts'
import { timeFormat, elapsedTime } from '@/utils/baseMixins'

defineProps({
  user: { type: Object as PropType<User>, required: true },
})

const router = useRouter()
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormCheck />
    </CTableDataCell>
    <CTableDataCell>
      <router-link :to="{ name: '사용자 - 보기', params: { userId: user.pk } }">
        {{ user.username }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ user.profile?.name }}</CTableDataCell>
    <CTableDataCell>{{ user.email }}</CTableDataCell>
    <CTableDataCell>{{ user.is_superuser ? '예' : '아니오' }}</CTableDataCell>
    <CTableDataCell>{{ timeFormat(user.date_joined) }}</CTableDataCell>
    <CTableDataCell>{{ elapsedTime(user.last_login as string) }}</CTableDataCell>
    <CTableDataCell>
      <span>
        <CDropdown color="secondary" variant="input-group" placement="bottom-end">
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
                <v-icon icon="mdi-pencil" color="yellow-darken-2" size="sm" />
                편집
              </span>
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </span>
    </CTableDataCell>
  </CTableRow>
</template>
