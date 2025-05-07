<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { type Company } from '@/store/types/settings'
import { useAccount } from '@/store/pinia/account'
import { write_company_settings } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ company: { type: Object as PropType<Company>, default: null } })

const emit = defineEmits(['create-form', 'update-form'])

const refAlertModal = ref()

const toEdit = () => {
  if (write_company_settings.value) emit('update-form')
  else refAlertModal.value.callModal()
}

const account = useAccount()

const toCreate = () => {
  if (account.superAuth) emit('create-form')
  else refAlertModal.value.callModal()
}
</script>

<template>
  <CCardBody>
    <CRow>
      <CCol class="pt-2">
        <CTable hover responsive>
          <colgroup>
            <col style="width: 25%" />
            <col style="width: 75%" />
          </colgroup>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 회사명</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.name }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 대표자명</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.ceo }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                사업자등록번호
              </CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.tax_number }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                법인등록번호
              </CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.org_number }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 업태</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.business_cond }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 종목</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.business_even }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 설립일자</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.es_date }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 개업일자</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.op_date }}</span>
              </CTableDataCell>
            </CTableRow>

            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary"> 회사주소</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">
                  <span v-if="company.zipcode">({{ company.zipcode }})</span>
                  {{ company.address1 }} {{ company.address2 }}
                  {{ company.address3 }}
                </span>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCol>
    </CRow>
  </CCardBody>

  <CCardFooter v-if="write_company_settings">
    <CRow class="justify-content-between">
      <CCol xs="auto">
        <v-btn type="button" color="success" :disabled="!company" @click="toEdit">
          <v-icon icon="mdi mdi-check-circle-outline" size="small" />
          수정하기
        </v-btn>
      </CCol>
      <CCol xs="auto">
        <v-btn type="button" color="primary" @click="toCreate">
          <v-icon icon="mdi mdi-check-circle-outline" size="small" />
          등록하기
        </v-btn>
      </CCol>
    </CRow>
  </CCardFooter>

  <AlertModal ref="refAlertModal" />
</template>
