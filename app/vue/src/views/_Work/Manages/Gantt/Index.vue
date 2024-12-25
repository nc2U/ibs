<script setup lang="ts">
import { computed, type ComputedRef, inject, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { getToday } from '@/utils/baseMixins'
import type { Company } from '@/store/types/settings'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'

const cBody = ref()
const company = inject<ComputedRef<Company>>('company')
const isDark = inject<ComputedRef<boolean>>('isDark')

const comName = computed(() => company?.value?.name)

const route = useRoute()

const sideNavCAll = () => cBody.value.toggle()

const row1BarList = ref([
  {
    sDate: '2024-12-13 00:00',
    eDate: '2024-12-23 00:00',
    ganttBarConfig: {
      // each bar must have a nested ganttBarConfig object ...
      id: 'unique-id-1', // ... and a unique "id" property
      label: '0%',
    },
  },
])
const row2BarList = ref([
  {
    sDate: '2024-12-13 00:00',
    eDate: '2025-02-10 00:00',
    ganttBarConfig: {
      id: 'another-unique-id-2',
      hasHandles: true,
      label: '0%',
      style: {
        // arbitrary CSS styling for your bar
        background: 'lightgreen',
        borderRadius: '20px',
        color: 'red',
      },
    },
  },
])
</script>

<template>
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ route.name }}</h5>
        </CCol>
      </CRow>

      <SearchList />

      <CRow class="mb-3">
        <CCol>
          <g-gantt-chart
            :style="`border-bottom: #${isDark ? '666' : 'ddd'} 1px solid`"
            :current-time-label="getToday()"
            label-column-title="[인천] 석남동 조합"
            chart-start="2024-12-01 00:00"
            chart-end="2025-05-31 00:00"
            precision="week"
            bar-start="sDate"
            bar-end="eDate"
            current-time
            label-column-width="450px"
            row-height="20"
            :color-scheme="isDark ? 'slumber' : ''"
            grid
          >
            <g-gantt-row label="토지 목록 작성" :bars="row1BarList" />
            <g-gantt-row label="토지 매입 완료" :bars="row2BarList" />
            <g-gantt-row v-for="i in 10" label="" :bars="[]" :key="i" />
          </g-gantt-chart>
        </CCol>
      </CRow>

      <CRow>
        <CCol>
          <CButtonGroup role="group">
            <CButton color="primary" variant="outline" size="sm">« 뒤로</CButton>
            <CButton color="primary" variant="outline" size="sm">다음 »</CButton>
          </CButtonGroup>
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
