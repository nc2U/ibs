<script lang="ts" setup>
import { ref } from 'vue'
import DashboardGrid from './components/DashboardGrid.vue'
import WidgetConfigPanel from './components/WidgetConfigPanel.vue'

const showConfigPanel = ref(false)
</script>

<template>
  <CContainer fluid>
    <CRow class="mt-3 mb-2">
      <CCol class="d-flex justify-content-between align-items-center">
        <h5 class="px-3 mb-0"></h5>
        <v-btn
          variant="outlined"
          color="primary"
          size="small"
          prepend-icon="mdi-view-dashboard-edit"
          @click="showConfigPanel = true"
        >
          위젯 설정
        </v-btn>
      </CCol>
    </CRow>

    <CRow>
      <CCol>
        <DashboardGrid />
      </CCol>
    </CRow>

    <WidgetConfigPanel v-model="showConfigPanel" />
  </CContainer>
</template>
