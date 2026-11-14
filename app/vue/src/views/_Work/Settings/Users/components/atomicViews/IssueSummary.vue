<script lang="ts" setup>
import { useRoute } from 'vue-router'

interface IssueNum {
  open_charged?: number
  closed_charged?: number
  all_charged?: number
  open_created?: number
  closed_created?: number
  all_created?: number
}

withDefaults(
  defineProps<{
    issueNum?: IssueNum
  }>(),
  {
    issueNum: () => ({}),
  },
)

const route = useRoute()
</script>

<template>
  <CRow class="mb-3">
    <CCol>
      <v-divider class="mb-0" />
      <CTable small striped hover responsive class="text-center">
        <CTableHead>
          <CTableRow>
            <CTableHeaderCell></CTableHeaderCell>
            <CTableHeaderCell>진행중</CTableHeaderCell>
            <CTableHeaderCell>완료됨</CTableHeaderCell>
            <CTableHeaderCell>합계</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow>
            <CTableDataCell class="text-start">
              <router-link :to="{ name: '업무', query: { assignee: route.params.userId } }">
                할당된 업무
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{ name: '업무', query: { status: 'open', assignee: route.params.userId } }"
              >
                {{ issueNum.open_charged }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{
                  name: '업무',
                  query: { status: 'closed', assignee: route.params.userId },
                }"
              >
                {{ issueNum.closed_charged }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{
                  name: '업무',
                  query: { status: 'any', assignee: route.params.userId },
                }"
              >
                {{ issueNum.all_charged }}
              </router-link>
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableDataCell class="text-start">
              <router-link :to="{ name: '업무', query: { author: route.params.userId } }">
                작성한 업무
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{
                  name: '업무',
                  query: { status: 'open', author: route.params.userId },
                }"
              >
                {{ issueNum.open_created }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{
                  name: '업무',
                  query: { status: 'closed', author: route.params.userId },
                }"
              >
                {{ issueNum.closed_created }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{
                  name: '업무',
                  query: { status: 'any', author: route.params.userId },
                }"
              >
                {{ issueNum.all_created }}
              </router-link>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
