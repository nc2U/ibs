<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { User } from '@/store/types/accounts'
import { useAccount } from '@/store/pinia/account.ts'
import NoData from '@/components/NoData/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import UserItem from '@/views/_Work/Settings/Users/components/UserItem.vue'
import TextButton from '../../../components/atomics/TextButton.vue'

defineProps({
  userList: { type: Array as PropType<User[]>, default: () => [] },
})

const route = useRoute()

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ route.name }}</h5>
    </CCol>

    <CCol v-if="workManager" class="text-right">
      <span class="mr-2">
        <TextButton name="새 사용자" :to="{ name: '사용자 - 생성' }" />
      </span>

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
            <CDropdownItem>
              <TextButton name="가져오기" icon="mdi-file-document-arrow-right" color="secondary" />
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </span>
    </CCol>
  </CRow>

  <SearchList />

  <NoData v-if="!userList.length" />

  <CRow v-else>
    <CCol>
      <v-divider class="mb-0" />
      <CTable hover small striped responsive>
        <CTableHead>
          <CTableRow color="">
            <CTableHeaderCell>
              <CFormCheck />
            </CTableHeaderCell>
            <CTableHeaderCell>아이디</CTableHeaderCell>
            <CTableHeaderCell>이름</CTableHeaderCell>
            <CTableHeaderCell>메일</CTableHeaderCell>
            <CTableHeaderCell>관리자</CTableHeaderCell>
            <CTableHeaderCell>등록</CTableHeaderCell>
            <CTableHeaderCell>마지막 로그인</CTableHeaderCell>
            <CTableHeaderCell></CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <UserItem v-for="user in userList" :key="user.pk" :user="user" />
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
