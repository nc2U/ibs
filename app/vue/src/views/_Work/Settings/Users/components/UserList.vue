<script lang="ts" setup>
import { computed, ref, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { User } from '@/store/types/accounts'
import { useAccount } from '@/store/pinia/account'
import NoData from '@/components/NoData/Index.vue'
import UserItem from './UserItem.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  userList: { type: Array as PropType<User[]>, default: () => [] },
})

const route = useRoute()

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)

const activeFilter = ref<'all' | 'active' | 'inactive'>('active')
const searchKeyword = ref('')

const filteredUsers = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return props.userList.filter(u => {
    if (activeFilter.value === 'active' && !u.is_active) return false
    if (activeFilter.value === 'inactive' && u.is_active) return false
    if (!keyword) return true
    return (
      (u.username || '').toLowerCase().includes(keyword) ||
      (u.email || '').toLowerCase().includes(keyword) ||
      (u.profile?.name || '').toLowerCase().includes(keyword)
    )
  })
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <v-icon
          icon="mdi-account-multiple-plus-outline"
          color="blue-grey-lighten-1"
          size="small"
          class="me-2"
        />
        {{ route.name }}
      </h5>
    </CCol>

    <CCol v-if="workManager" class="text-end">
      <span class="me-2">
        <TextButton name="새 사용자" :to="{ name: '사용자 - 생성' }" />
      </span>
    </CCol>
  </CRow>

  <CRow class="mb-3 align-items-center g-2">
    <CCol sm="4" md="3" lg="2">
      <CFormSelect v-model="activeFilter" size="sm" aria-label="활성 상태 필터">
        <option value="active">활성 사용자</option>
        <option value="inactive">비활성 사용자</option>
        <option value="all">전체 사용자</option>
      </CFormSelect>
    </CCol>
    <CCol sm="6" md="4" lg="3">
      <CFormInput
        v-model="searchKeyword"
        size="sm"
        placeholder="아이디 / 이름 / 이메일 검색"
      />
    </CCol>
  </CRow>

  <NoData v-if="!filteredUsers.length" />

  <CRow v-else>
    <CCol>
      <v-divider class="mb-0" />
      <CTable hover striped responsive align="middle">
        <CTableHead>
          <CTableRow>
            <CTableHeaderCell>아이디</CTableHeaderCell>
            <CTableHeaderCell>이름</CTableHeaderCell>
            <CTableHeaderCell>메일</CTableHeaderCell>
            <CTableHeaderCell>상태</CTableHeaderCell>
            <CTableHeaderCell>관리자</CTableHeaderCell>
            <CTableHeaderCell>등록</CTableHeaderCell>
            <CTableHeaderCell>마지막 로그인</CTableHeaderCell>
            <CTableHeaderCell></CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <UserItem v-for="user in filteredUsers" :key="user.pk" :user="user" />
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
