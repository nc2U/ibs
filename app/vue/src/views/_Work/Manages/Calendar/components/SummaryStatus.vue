<script lang="ts" setup>
import type { PropType } from 'vue'

defineProps({
  summary: {
    type: Object as PropType<{ total: number; open: number; closed: number }>,
    required: true,
  },
  title: {
    type: String,
    default: '이번 달 업무 현황',
  },
})
</script>

<template>
  <v-card variant="outlined" class="mt-4 pa-4 border-dashed rounded-lg">
    <CRow align="center">
      <CCol md="4" class="border-right d-none d-md-block">
        <div class="text-subtitle-2 text-grey mb-2">{{ title }}</div>
        <div class="d-flex justify-space-around align-center">
          <div class="text-center">
            <div class="text-h6 fw-bold">{{ summary.total }}</div>
            <div class="text-caption text-grey">전체</div>
          </div>
          <div class="text-center">
            <div class="text-h6 fw-bold text-info">{{ summary.open }}</div>
            <div class="text-caption text-grey">진행중</div>
          </div>
          <div class="text-center">
            <div class="text-h6 fw-bold text-success">{{ summary.closed }}</div>
            <div class="text-caption text-grey">완료</div>
          </div>
        </div>
      </CCol>
      <CCol md="8" class="pl-md-6">
        <div class="text-subtitle-2 text-grey mb-2">일정 가이드</div>
        <div class="d-flex flex-wrap gap-4">
          <div class="d-flex align-center me-4">
            <v-icon icon="mdi-arrow-right-bold" color="success" size="small" class="me-1" />
            <span class="text-body-2">오늘 시작</span>
          </div>
          <div class="d-flex align-center mr-4">
            <v-icon icon="mdi-arrow-left-bold" color="danger" size="small" class="mr-1" />
            <span class="text-body-2">오늘 종료</span>
          </div>
          <div class="d-flex align-center">
            <v-icon icon="mdi-rhombus" color="danger" size="small" class="mr-1" />
            <span class="text-body-2">오늘 시작/종료</span>
          </div>
        </div>
        <div class="mt-2 text-caption text-grey-darken-1">
          * 바(Bar)의 색상은 업무의 현재 상태(신규/진행/완료 등)를 나타냅니다.
        </div>
      </CCol>
    </CRow>
  </v-card>
</template>
