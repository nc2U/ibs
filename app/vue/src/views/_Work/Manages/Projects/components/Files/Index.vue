<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)

const route = useRoute()
watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) console.log(nVal)
  },
)

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>파일</h5>
        </CCol>

        <CCol class="text-right">
          <span v-if="issueProject?.status !== '9'" class="mr-2 form-text">
            <v-icon icon="mdi-plus-circle" color="success" size="15" class="mr-1" />
            <router-link to="" class="ml-1">파일추가</router-link>
          </span>
        </CCol>
      </CRow>

      <CRow>
        <CCol>
          <v-divider class="mb-0" />
          <CTable small>
            <CTableHead>
              <CTableRow class="text-center">
                <CTableHeaderCell>파일</CTableHeaderCell>
                <CTableHeaderCell>날짜</CTableHeaderCell>
                <CTableHeaderCell>크기</CTableHeaderCell>
                <CTableHeaderCell>D/L</CTableHeaderCell>
                <CTableHeaderCell>Checksum</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
          </CTable>
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
