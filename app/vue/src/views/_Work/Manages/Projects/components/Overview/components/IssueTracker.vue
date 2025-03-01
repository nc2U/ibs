<script lang="ts" setup>
import { inject, type PropType } from 'vue'

const props = defineProps({
  trackers: { type: Array as PropType<{ pk: number; name: string }[]>, default: () => [] },
  trackerSummary: {
    type: Array as PropType<{ pk: number; name: string; open: number; closed: number }[]>,
    default: () => [],
  },
})

const isDark = inject('isDark')

const getSummary = (pk: number) => props.trackerSummary.filter(t => t.pk === pk)[0]
</script>

<template>
  <CCard :color="isDark ? '' : 'light'">
    <CCardBody>
      <CCardSubtitle class="mb-2">
        <v-icon icon="mdi-briefcase-edit" size="sm" color="grey" class="mr-1" />
        업무 추적
      </CCardSubtitle>
      <CTable bordered hover small striped class="mt-2 mb-0">
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell scope="col"></CTableHeaderCell>
            <CTableHeaderCell scope="col">진행중</CTableHeaderCell>
            <CTableHeaderCell scope="col">완료됨</CTableHeaderCell>
            <CTableHeaderCell scope="col">합계</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="tracker in trackers" :key="tracker.pk" class="text-center">
            <CTableHeaderCell>
              <router-link :to="{ name: '(업무)', query: { tracker: tracker.pk } }">
                {{ tracker.name }}
              </router-link>
            </CTableHeaderCell>
            <CTableDataCell>
              <router-link :to="{ name: '(업무)', query: { tracker: tracker.pk } }">
                {{ getSummary(tracker.pk)?.open ?? 0 }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link
                :to="{ name: '(업무)', query: { status: 'closed', tracker: tracker.pk } }"
              >
                {{ getSummary(tracker.pk)?.closed ?? 0 }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell>
              <router-link :to="{ name: '(업무)', query: { status: 'any', tracker: tracker.pk } }">
                {{ (getSummary(tracker.pk)?.open ?? 0) + (getSummary(tracker.pk)?.closed ?? 0) }}
              </router-link>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCardBody>

    <CCardText class="mx-3 mb-2 form-text">
      <router-link :to="{ name: '(업무)' }">모든 업무 보기</router-link>
      <span class="px-2">|</span>
      <router-link :to="{ name: '(업무) - 보고서' }"> 요약</router-link>
      <span class="px-2">|</span>
      <router-link :to="{ name: '(달력)' }"> 달력</router-link>
      <span class="px-2">|</span>
      <router-link :to="{ name: '(간트차트)' }"> Gantt 차트</router-link>
    </CCardText>
  </CCard>
</template>
