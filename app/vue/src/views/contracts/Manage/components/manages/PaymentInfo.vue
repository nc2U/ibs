<script lang="ts" setup>
import { type PropType } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import type { Contract } from '@/store/types/contract'
import { useDownload } from '@/composables/useDownload'
import { CCard } from '@coreui/vue'

defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
})

// 다운로드 컴포저블 사용
const { downloadFile, downloadPDF, downloadExcel } = useDownload()

// 통합 파일 다운로드 핸들러
const handleFileDownload = (url: string, fileName: string) => {
  downloadFile(url, fileName)
}

// 타입별 다운로드 핸들러 (호환성)
const handlePDFDownload = (url: string, fileName: string) => {
  downloadPDF(url, fileName)
}

const handleExcelDownload = (url: string, fileName: string) => {
  downloadExcel(url, fileName)
}
</script>

<template>
  <!-- 금액 정보 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>금액 정보</strong>
    </CCardHeader>
    <CCardBody>
      <div class="mb-3">
        <strong class="d-block mb-2">분양가</strong>
        <div class="display-6 text-primary">
          {{ numFormat(contract.contractprice?.price || 0) }} 원
        </div>
      </div>
      <CRow class="mb-2">
        <CCol :cols="6">
          <small class="text-muted">건물가:</small>
          <div>{{ numFormat(contract.contractprice?.price_build || 0) }}</div>
        </CCol>
        <CCol :cols="6">
          <small class="text-muted">토지가:</small>
          <div>{{ numFormat(contract.contractprice?.price_land || 0) }}</div>
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CCol :cols="6">
          <small class="text-muted">부가세:</small>
          <div>{{ numFormat(contract.contractprice?.price_tax || 0) }}</div>
        </CCol>
      </CRow>
      <hr />
      <CRow class="mb-2">
        <CCol :cols="6">
          <strong>총 납부액:</strong>
        </CCol>
        <CCol :cols="6" class="text-end">
          <strong class="text-success">{{ numFormat(contract.total_paid) }} 원</strong>
        </CCol>
      </CRow>
      <CRow>
        <CCol :cols="6">
          <strong>마지막 납부:</strong>
        </CCol>
        <CCol :cols="6" class="text-end">
          <span>{{ contract.last_paid_order?.__str__ || '-' }}</span>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>

  <!-- 납부 내역 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>납부 내역</strong>
    </CCardHeader>
    <CCardBody>
      <div v-if="contract.payments && contract.payments.length > 0">
        <CTable small striped hover>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell>납부일</CTableHeaderCell>
              <CTableHeaderCell>회차</CTableHeaderCell>
              <CTableHeaderCell class="text-end">금액</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow v-for="payment in contract.payments" :key="payment.pk">
              <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
              <CTableDataCell>{{ payment.installment_order.__str__ }}</CTableDataCell>
              <CTableDataCell class="text-end">
                {{ numFormat(payment.income) }}
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
        <div class="text-right">
          <router-link
            :to="{
              name: '건별 수납 내역',
              params: { contractId: contract.pk },
            }"
          >
            건별 수납 관리 <v-icon icon="mdi-arrow-right" size="18" />
          </router-link>
        </div>
      </div>
      <div v-else class="text-center text-muted py-3">납부 내역이 없습니다.</div>
    </CCardBody>
  </CCard>

  <!-- 각종 증명 확인서 출력 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>고지 / 확인서 발급</strong>
    </CCardHeader>
    <CCardBody>
      <div>
        <CTable small striped hover>
          <CTableHead>
            <CTableRow class="text-center">
              <CTableHeaderCell>구분</CTableHeaderCell>
              <CTableHeaderCell>발급 문서</CTableHeaderCell>
              <CTableHeaderCell>비고</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow>
              <CTableDataCell class="text-center">
                <CFormCheck />
              </CTableDataCell>
              <CTableDataCell>
                <button
                  @click="handleFileDownload(`/pdf/bill/?project=${contract.project}&seq=${contract.pk}`, '대금수납_고지서.pdf')"
                  class="btn btn-link p-0 text-start"
                  style="text-decoration: none;"
                >
                  대금수납 고지서
                </button>
              </CTableDataCell>
              <CTableDataCell></CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableDataCell class="text-center">
                <CFormCheck />
              </CTableDataCell>
              <CTableDataCell>
                <button
                  @click="handleFileDownload(`/pdf/payments/?project=${contract.project}&contract=${contract.pk}&is_calc=1`, '납부내역_확인서_일반.pdf')"
                  class="btn btn-link p-0 text-start"
                  style="text-decoration: none;"
                >
                  납부내역 확인서(일반)
                </button>
              </CTableDataCell>
              <CTableDataCell>할인/가산 내역 포함</CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableDataCell class="text-center">
                <CFormCheck />
              </CTableDataCell>
              <CTableDataCell>
                <button
                  @click="handleFileDownload(`/pdf/payments/?project=${contract.project}&contract=${contract.pk}`, '납부내역_확인서_확인.pdf')"
                  class="btn btn-link p-0 text-start"
                  style="text-decoration: none;"
                >
                  납부내역 확인서(확인)
                </button>
              </CTableDataCell>
              <CTableDataCell>대외 확인용</CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableDataCell class="text-center">
                <CFormCheck />
              </CTableDataCell>
              <CTableDataCell>
                <button
                  @click="handleFileDownload(`/pdf/calculation/?project=${contract.project}&contract=${contract.pk}`, '할인_가산금 내역서.pdf')"
                  class="btn btn-link p-0 text-start"
                  style="text-decoration: none;"
                >
                  할인/가산금 내역서
                </button>
              </CTableDataCell>
              <CTableDataCell></CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableDataCell class="text-center">
                <CFormCheck />
              </CTableDataCell>
              <CTableDataCell>
                <button
                  @click="handleFileDownload(`/pdf/cert-occupancy/?project=${contract.project}&contract=${contract.pk}`, '주택_인도_증서.pdf')"
                  class="btn btn-link p-0 text-start"
                  style="text-decoration: none;"
                >
                  주택 인도 증서
                </button>
              </CTableDataCell>
              <CTableDataCell></CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </div>
    </CCardBody>
  </CCard>
</template>
