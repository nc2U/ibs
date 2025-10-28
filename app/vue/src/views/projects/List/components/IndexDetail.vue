<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import { type Project } from '@/store/types/project'
import { numFormat } from '@/utils/baseMixins'
import { areaM2PyFormat, ratioFormat } from '@/utils/areaMixins'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ project: { type: Object as PropType<Project>, required: true } })

const emit = defineEmits(['create-form', 'update-form'])

const refAlertModal = ref()

const toCreate = () => {
  if (write_project.value) emit('create-form')
  else refAlertModal.value.callModal()
}
const toUpdate = () => {
  if (write_project.value) emit('update-form')
  else refAlertModal.value.callModal()
}
</script>

<template>
  <CCardBody>
    <CRow>
      <CCol class="pt-2">
        <CTable v-if="project" hover responsive>
          <colgroup>
            <col style="width: 15%" />
            <col style="width: 30%" />
            <col style="width: 15%" />
            <col style="width: 40%" />
          </colgroup>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 프로젝트명</CTableHeaderCell>
              <CTableDataCell>
                <span>
                  {{ project.name }}
                  <span v-if="project.start_year"> ({{ project.start_year }}년도) </span>
                </span>
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                프로젝트 종류
              </CTableHeaderCell>
              <CTableDataCell>
                {{ project.kind_desc }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 대지위치 </CTableHeaderCell>
              <CTableDataCell colspan="3">
                {{ project.location }}
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                용도지역지구
              </CTableHeaderCell>
              <CTableDataCell>
                {{ project.area_usage }}
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 건축규모</CTableHeaderCell>
              <CTableDataCell>
                {{ project.build_size }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                세대(호/실)수
              </CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ numFormat(project.num_unit as number) }}
                <span v-if="project.num_unit">세대(호/실)</span>
              </CTableDataCell>

              <CTableHeaderCell scope="row" :color="TableSecondary">
                대지매입면적
              </CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.buy_land_extent as number) }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                계획대지면적
              </CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.scheme_land_extent as number) }}
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                기부채납면적
              </CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.donation_land_extent as number) }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 지상연면적</CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.on_floor_area as number) }}
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 지하연면적</CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.under_floor_area as number) }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 총 연면적</CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.total_floor_area as number) }}
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 건축면적</CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ areaM2PyFormat(project.build_area as number) }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 용적율</CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ ratioFormat(project.floor_area_ratio as number) }}
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 건폐율</CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ ratioFormat(project.build_to_land_ratio as number) }}
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                법정주차대수
              </CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ numFormat(project.num_legal_parking as number) }}
                <span v-if="project.num_legal_parking">대</span>
              </CTableDataCell>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                계획주차대수
              </CTableHeaderCell>
              <CTableDataCell class="text-right pr-3">
                {{ numFormat(project.num_planed_parking as number) }}
                <span v-if="project.num_planed_parking">대</span>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCol>
    </CRow>
  </CCardBody>

  <CCardFooter v-if="write_project">
    <CRow class="justify-content-between">
      <CCol xs="auto">
        <v-btn type="button" color="success" :disabled="!project" @click="toUpdate">
          <CIcon name="cil-check-circle" />
          수정하기
        </v-btn>
      </CCol>
      <CCol xs="auto">
        <v-btn type="button" color="primary" @click="toCreate">
          <CIcon name="cil-check-circle" />
          등록하기
        </v-btn>
      </CCol>
    </CRow>
  </CCardFooter>

  <AlertModal ref="refAlertModal" />
</template>
