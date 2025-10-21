<script lang="ts" setup>
import { computed, inject, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins'
import { write_contract } from '@/utils/pageAuth'
import { useContract } from '@/store/pinia/contract'
import type { Contract, Contractor } from '@/store/types/contract'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object as PropType<Contract>, default: null },
  contractor: { type: Object as PropType<Contractor>, default: null },
  fromPage: { type: [Number, null] as PropType<number | null>, default: null },
})

const router = useRouter()
const isDark = inject('isDark')

const contStore = useContract()
const addressList = computed(() => contStore.contAddressList)
const currentAddress = computed(() => addressList.value.find(addr => addr.is_current))

// 계약 정보가 있는지 확인
const hasContract = computed(() => !!props.contract && !!props.contractor)

// 자격구분 색상
const getQualificationColor = (q: '1' | '2' | '3' | '4' | '') => {
  if (!q) return 'secondary'
  return { '1': 'info', '2': 'warning', '3': 'success', '4': 'danger' }[q]
}

// 계약자 상태 텍스트
const getStatusText = (status: '1' | '2' | '3' | '4' | '5' | '') => {
  if (!status) return '-'
  return {
    '1': '청약',
    '2': '계약',
    '3': '해지',
    '4': '승계(매도)',
    '5': '승계(매수)',
  }[status]
}

// 목록으로 돌아가기
const goBack = () => {
  if (props.fromPage) {
    router.push({ name: '계약 내역 조회', query: { page: props.fromPage } })
  } else {
    router.push({ name: '계약 내역 조회' })
  }
}
</script>

<template>
  <div v-if="!hasContract" class="text-center py-5">
    <p class="text-muted">계약자를 선택하여 계약 정보를 조회하세요.</p>
  </div>

  <div v-else>
    <!-- 상단 액션 바 -->
    <CRow class="mb-3">
      <CCol>
        <div class="d-flex justify-content-between align-items-center">
          <v-btn color="secondary" size="small" @click="goBack">
            <v-icon icon="mdi-arrow-left" class="mr-1" />
            목록으로
          </v-btn>
          <div v-if="write_contract">
            <v-btn color="primary" size="small" class="mr-2">
              <v-icon icon="mdi-pencil" class="mr-1" />
              수정
            </v-btn>
            <v-btn color="danger" size="small">
              <v-icon icon="mdi-delete" class="mr-1" />
              삭제
            </v-btn>
          </div>
        </div>
      </CCol>
    </CRow>

    <!-- 2단 컬럼 레이아웃 -->
    <CRow>
      <!-- 왼쪽 컬럼 -->
      <CCol :md="8" :lg="7">
        <!-- 계약 기본 정보 카드 -->
        <CCard class="mb-3">
          <CCardHeader>
            <strong>계약 기본 정보</strong>
          </CCardHeader>
          <CCardBody>
            <CRow class="mb-2">
              <CCol :sm="6">
                <strong>계약번호:</strong>
                <span class="ml-2">{{ contract.serial_number }}</span>
              </CCol>
              <CCol :sm="6">
                <strong>분양차수:</strong>
                <span class="ml-2">{{ contract.order_group_desc.name }}</span>
              </CCol>
            </CRow>
            <CRow class="mb-2">
              <CCol :sm="6">
                <strong>타입:</strong>
                <CIcon
                  name="cibDiscover"
                  :style="'color:' + contract.unit_type_desc.color"
                  size="sm"
                  class="ml-2 mr-1"
                />
                <span>{{ contract.unit_type_desc.name }}</span>
              </CCol>
              <CCol :sm="6">
                <strong>호수:</strong>
                <span
                  class="ml-2"
                  :class="contract.key_unit?.houseunit ? 'text-success' : 'text-danger'"
                >
                  {{ contract.key_unit?.houseunit?.__str__ || '미정' }}
                </span>
              </CCol>
            </CRow>
            <CRow class="mb-2">
              <CCol :sm="6">
                <strong>계약일:</strong>
                <span class="ml-2">{{ contractor.contract_date || '-' }}</span>
              </CCol>
              <CCol :sm="6">
                <strong>공급계약일:</strong>
                <span class="ml-2">{{ contract.sup_cont_date || '-' }}</span>
              </CCol>
            </CRow>
            <CRow>
              <CCol :sm="6">
                <strong>활성화:</strong>
                <CBadge :color="contract.activation ? 'success' : 'secondary'" class="ml-2">
                  {{ contract.activation ? '활성' : '비활성' }}
                </CBadge>
              </CCol>
              <CCol :sm="6">
                <strong>공급계약:</strong>
                <CBadge :color="contract.is_sup_cont ? 'success' : 'secondary'" class="ml-2">
                  {{ contract.is_sup_cont ? '완료' : '미완료' }}
                </CBadge>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>

        <!-- 계약자 상세 정보 카드 -->
        <CCard class="mb-3">
          <CCardHeader>
            <strong>계약자 상세 정보</strong>
          </CCardHeader>
          <CCardBody>
            <!-- 기본 정보 -->
            <div class="mb-3 pb-3 border-bottom">
              <h6 class="mb-2">기본 정보</h6>
              <CRow class="mb-2">
                <CCol :sm="6">
                  <strong>이름:</strong>
                  <span class="ml-2">{{ contractor.name }}</span>
                </CCol>
                <CCol :sm="6">
                  <strong>생년월일:</strong>
                  <span class="ml-2">{{ contractor.birth_date }}</span>
                </CCol>
              </CRow>
              <CRow class="mb-2">
                <CCol :sm="6">
                  <strong>성별:</strong>
                  <span class="ml-2">{{ contractor.gender === 'M' ? '남성' : '여성' }}</span>
                </CCol>
                <CCol :sm="6">
                  <strong>자격구분:</strong>
                  <CBadge
                    :color="getQualificationColor(contractor.qualification)"
                    class="ml-2"
                  >
                    {{ contractor.qualifi_display }}
                  </CBadge>
                </CCol>
              </CRow>
              <CRow>
                <CCol :sm="6">
                  <strong>상태:</strong>
                  <span class="ml-2">{{ getStatusText(contractor.status) }}</span>
                </CCol>
                <CCol :sm="6">
                  <strong>청약일:</strong>
                  <span class="ml-2">{{ contractor.reservation_date || '-' }}</span>
                </CCol>
              </CRow>
            </div>

            <!-- 연락처 정보 -->
            <div
              v-if="contract.contractor?.contractorcontact"
              class="mb-3 pb-3 border-bottom"
            >
              <h6 class="mb-2">연락처</h6>
              <CRow class="mb-2">
                <CCol :sm="6">
                  <strong>휴대폰:</strong>
                  <span class="ml-2">
                    {{ contract.contractor.contractorcontact.cell_phone || '-' }}
                  </span>
                </CCol>
                <CCol :sm="6">
                  <strong>집전화:</strong>
                  <span class="ml-2">
                    {{ contract.contractor.contractorcontact.home_phone || '-' }}
                  </span>
                </CCol>
              </CRow>
              <CRow class="mb-2">
                <CCol :sm="6">
                  <strong>기타전화:</strong>
                  <span class="ml-2">
                    {{ contract.contractor.contractorcontact.other_phone || '-' }}
                  </span>
                </CCol>
                <CCol :sm="6">
                  <strong>이메일:</strong>
                  <span class="ml-2">
                    {{ contract.contractor.contractorcontact.email || '-' }}
                  </span>
                </CCol>
              </CRow>
            </div>

            <!-- 주소 정보 -->
            <div
              v-if="currentAddress || contract.contractor?.contractoraddress"
              class="mb-3 pb-3 border-bottom"
            >
              <h6 class="mb-2">주민등록 주소</h6>
              <div
                v-if="
                  (currentAddress && currentAddress.id_address1) ||
                  contract.contractor?.contractoraddress?.id_address1
                "
              >
                <div>
                  ({{
                    currentAddress?.id_zipcode ||
                    contract.contractor?.contractoraddress?.id_zipcode
                  }})
                  {{
                    currentAddress?.id_address1 ||
                    contract.contractor?.contractoraddress?.id_address1
                  }}
                </div>
                <div>
                  {{
                    currentAddress?.id_address2 ||
                    contract.contractor?.contractoraddress?.id_address2
                  }}
                  {{
                    currentAddress?.id_address3 ||
                    contract.contractor?.contractoraddress?.id_address3
                  }}
                </div>
              </div>
              <div v-else class="text-muted">주소 정보가 없습니다.</div>
            </div>

            <div
              v-if="currentAddress || contract.contractor?.contractoraddress"
              class="mb-3 pb-3 border-bottom"
            >
              <h6 class="mb-2">우편물 수령 주소</h6>
              <div
                v-if="
                  (currentAddress && currentAddress.dm_address1) ||
                  contract.contractor?.contractoraddress?.dm_address1
                "
              >
                <div>
                  ({{
                    currentAddress?.dm_zipcode ||
                    contract.contractor?.contractoraddress?.dm_zipcode
                  }})
                  {{
                    currentAddress?.dm_address1 ||
                    contract.contractor?.contractoraddress?.dm_address1
                  }}
                </div>
                <div>
                  {{
                    currentAddress?.dm_address2 ||
                    contract.contractor?.contractoraddress?.dm_address2
                  }}
                  {{
                    currentAddress?.dm_address3 ||
                    contract.contractor?.contractoraddress?.dm_address3
                  }}
                </div>
              </div>
              <div v-else class="text-muted">주소 정보가 없습니다.</div>
            </div>

            <!-- 메모 -->
            <div>
              <h6 class="mb-2">메모</h6>
              <div class="text-muted">{{ contractor.note || '메모가 없습니다.' }}</div>
            </div>
          </CCardBody>
        </CCard>
      </CCol>

      <!-- 오른쪽 컬럼 -->
      <CCol :md="4" :lg="5">
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
                <small class="text-muted">세금:</small>
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
            </div>
            <div v-else class="text-center text-muted py-3">납부 내역이 없습니다.</div>
          </CCardBody>
        </CCard>

        <!-- 계약 파일 관리 카드 -->
        <CCard>
          <CCardHeader>
            <strong>계약 파일</strong>
          </CCardHeader>
          <CCardBody>
            <div v-if="contract.contract_files && contract.contract_files.length > 0">
              <div
                v-for="file in contract.contract_files"
                :key="file.pk"
                class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded"
              >
                <div class="flex-grow-1">
                  <div>
                    <v-icon icon="mdi-file-document" size="small" class="mr-1" />
                    <strong>{{ file.file_name }}</strong>
                  </div>
                  <small class="text-muted">
                    {{ (file.file_size / 1024).toFixed(2) }} KB
                    <span class="mx-1">|</span>
                    {{ file.created }}
                    <span class="mx-1">|</span>
                    {{ file.creator.username }}
                  </small>
                </div>
                <div>
                  <a :href="file.file" target="_blank" class="text-decoration-none">
                    <v-icon icon="mdi-download" color="primary" />
                  </a>
                  <v-icon
                    v-if="write_contract"
                    icon="mdi-delete"
                    color="danger"
                    class="ml-2 pointer"
                  />
                </div>
              </div>
            </div>
            <div v-else class="text-center text-muted py-3">
              <v-icon icon="mdi-file-document-outline" size="large" class="mb-2" />
              <div>등록된 파일이 없습니다.</div>
            </div>
            <div v-if="write_contract" class="mt-3">
              <v-btn color="primary" block size="small">
                <v-icon icon="mdi-upload" class="mr-1" />
                파일 업로드
              </v-btn>
            </div>
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  </div>
</template>

<style scoped>
.pointer {
  cursor: pointer;
}
</style>
