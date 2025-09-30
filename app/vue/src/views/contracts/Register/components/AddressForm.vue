<script lang="ts" setup>
import { inject, ref } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import { CForm, CModalBody, CTableBody, CTableDataCell } from '@coreui/vue'

defineProps({
  address: { type: Object, default: () => ({}) },
  past_addresses: { type: Array, default: () => [] },
})

const refModalPost = ref()

const isDark = inject('isDark')

const toSame = () => {}
const addressCallback = () => 1
</script>

<template>
  <CForm>
    <CModalBody class="text-body">
      <h6>변경할 주소</h6>
      <CRow class="mb-3">
        <CFormLabel sm="2" class="col-lg-1 col-form-label required"> 주민등록</CFormLabel>

        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CInputGroup>
            <CInputGroupText @click="refModalPost.initiate(1)"> 우편번호</CInputGroupText>
            <CFormInput
              v-maska
              data-maska="#####"
              maxlength="5"
              placeholder="우편번호"
              required
              @focus="refModalPost.initiate(1)"
            />
            <CFormFeedback invalid>우편번호를 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>
        <CCol sm="12" md="6" lg="4" class="mb-lg-0">
          <CFormInput
            maxlength="35"
            placeholder="주민등록 주소를 입력하세요"
            required
            @focus="refModalPost.initiate(1)"
          />
        </CCol>

        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CFormInput ref="address21" maxlength="50" placeholder="상세주소를 입력하세요" />
        </CCol>

        <CCol sm="12" md="6" lg="2">
          <CFormInput maxlength="30" placeholder="참고항목을 입력하세요" />
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CFormLabel sm="2" class="col-lg-1 col-form-label required"> 우편수령</CFormLabel>
        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CInputGroup>
            <CInputGroupText @click="refModalPost.initiate(2)"> 우편번호</CInputGroupText>
            <CFormInput
              v-maska
              data-maska="#####"
              maxlength="5"
              placeholder="우편번호"
              required
              @focus="refModalPost.initiate(2)"
            />
          </CInputGroup>
        </CCol>
        <CCol sm="12" md="6" lg="4" class="mb-lg-0">
          <CFormInput
            maxlength="50"
            placeholder="우편물 수령 주소를 입력하세요"
            required
            @focus="refModalPost.initiate(2)"
          />
        </CCol>
        <CCol sm="12" md="6" lg="2" class="mb-lg-0">
          <CFormInput ref="address22" maxlength="50" placeholder="상세주소를 입력하세요" />
          <CFormFeedback invalid>상세주소를 입력하세요.</CFormFeedback>
        </CCol>
        <CCol sm="12" md="6" lg="2">
          <CFormInput maxlength="30" placeholder="참고항목을 입력하세요" />
        </CCol>
        <CCol sm="12" lg="1" class="pt-1">
          <v-checkbox-btn
            id="to-same-for-modal"
            label="상동"
            density="compact"
            :color="isDark ? '#857DCC' : '#321FDB'"
            @click="toSame"
          />
          <!--            :disabled="!form.id_zipcode"-->
        </CCol>
      </CRow>
      <v-divider />
      <h6>변경전 (현재) 주소</h6>
      <CTable borderless responsive align="middle" class="mb-0" color="warning">
        <CTableBody class="text-center">
          <CTableRow>
            <CTableHeaderCell>주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              ({{ address.id_zipcode }}) {{ address.id_address1 }} {{ address.id_address2 }}
              {{ address.id_address3 }}
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell>우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              ({{ address.dm_zipcode }}) {{ address.dm_address1 }} {{ address.dm_address2 }}
              {{ address.dm_address3 }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
      <v-divider />
      <h6>과거 주소</h6>
      <CTable v-if="past_addresses.length" bordered responsive align="middle" class="mb-0">
        <CTableBody class="text-center">
          <CTableRow>
            <CTableDataCell rowspan="2">3</CTableDataCell>
            <CTableHeaderCell>주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              (21111) 인천광역시 연수구 능허대로289번길 21 대성빌딩 4층 (동춘동)
            </CTableDataCell>
            <CTableDataCell rowspan="2">2025/02/01 등록</CTableDataCell>
            <CTableDataCell rowspan="2" class="text-left">
              <CFormCheck id="a3" label="이 주소로 변경" />
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell>우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              (21111) 인천광역시 연수구 능허대로289번길 21 대성빌딩 4층 (동춘동)
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
        <CTableBody class="text-center">
          <CTableRow>
            <CTableDataCell rowspan="2">2</CTableDataCell>
            <CTableHeaderCell>주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              (21111) 인천광역시 연수구 능허대로289번길 21 대성빌딩 4층 (동춘동)
            </CTableDataCell>
            <CTableDataCell rowspan="2">2025/02/01 등록</CTableDataCell>
            <CTableDataCell rowspan="2" class="text-left">
              <CFormCheck id="a2" label="이 주소로 변경" />
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell>우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              (21111) 인천광역시 연수구 능허대로289번길 21 대성빌딩 4층 (동춘동)
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
        <CTableBody class="text-center">
          <CTableRow>
            <CTableDataCell rowspan="2">1</CTableDataCell>
            <CTableHeaderCell>주민등록 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              (21111) 인천광역시 연수구 능허대로289번길 21 대성빌딩 4층 (동춘동)
            </CTableDataCell>
            <CTableDataCell rowspan="2">2025/02/01 등록</CTableDataCell>
            <CTableDataCell rowspan="2" class="text-left">
              <CFormCheck id="a1" label="이 주소로 변경" />
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell>우편수령 주소</CTableHeaderCell>
            <CTableDataCell class="pl-2 text-left">
              (21111) 인천광역시 연수구 능허대로289번길 21 대성빌딩 4층 (동춘동)
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CTable v-else borderless align="middle">
        <CTableBody>
          <CTableRow class="text-center">
            <CTableDataCell style="height: 100px; color: grey">
              현재 주소 이전 주소 데이터가 없습니다.
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CModalBody>
    <CModalFooter>
      <v-btn :color="btnLight" size="small" @click="$emit('close')">닫기</v-btn>
      <v-btn color="primary" size="small">확인</v-btn>
    </CModalFooter>
  </CForm>

  <DaumPostcode ref="refModalPost" @address-callback="addressCallback" />
</template>
