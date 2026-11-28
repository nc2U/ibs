<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { TableSecondary } from '@/utils/cssMixins'
import type { Company } from '@/store/types/settings'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({
  company: { type: Object as PropType<Company | null>, default: null },
})

const emit = defineEmits(['create-form', 'update-form'])

const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const account = useAccount()
const canManageCompany = computed(() => Boolean(account.superAuth))

const toEdit = () => {
  if (canManageCompany.value) emit('update-form')
  else refAlertModal.value?.callModal()
}

const toCreate = () => {
  if (canManageCompany.value) emit('create-form')
  else refAlertModal.value?.callModal()
}
</script>

<template>
  <CCardBody class="p-3 p-md-4">
    <CRow>
      <CCol class="pt-2">
        <CTable hover responsive>
          <colgroup>
            <col style="width: 25%" />
            <col style="width: 75%" />
          </colgroup>
          <CTableHead>
            <CTableRow class="bg-more-light border-top">
              <CTableHeaderCell scope="col">구분</CTableHeaderCell>
              <CTableHeaderCell scope="col">내용</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">회사명</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">
                  {{ company.name }}
                  <v-chip
                    v-if="company.is_default"
                    color="primary"
                    variant="tonal"
                    size="x-small"
                    class="ms-2"
                  >
                    메인 회사
                  </v-chip>
                </span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">영문 회사명</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.en_name || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">회사 약칭</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.short_name || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">대표자명</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.ceo || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                사업자등록번호
              </CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.tax_number || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">
                법인등록번호
              </CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.org_number || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">업태</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.business_cond || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">종목</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.business_even || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">설립일자</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.es_date || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">개업일자</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.op_date || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">대표전화 / 팩스</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">
                  {{ company.phone || '-' }}
                  <span v-if="company.fax" class="text-body-secondary ms-2">
                    (FAX: {{ company.fax }})
                  </span>
                </span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">대표이메일</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">{{ company.email || '-' }}</span>
              </CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell scope="row" :color="TableSecondary">회사주소</CTableHeaderCell>
              <CTableDataCell>
                <span v-if="company">
                  <template
                    v-if="
                      company.zipcode || company.address1 || company.address2 || company.address3
                    "
                  >
                    <span v-if="company.zipcode">({{ company.zipcode }})</span>
                    {{ company.address1 }} {{ company.address2 }}
                    {{ company.address3 }}
                  </template>
                  <template v-else>-</template>
                </span>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCol>
    </CRow>
  </CCardBody>

  <CCardFooter>
    <CRow v-if="canManageCompany" class="justify-content-between">
      <CCol xs="auto">
        <v-btn type="button" color="success" :disabled="!company" @click="toEdit">
          <v-icon icon="mdi-check-circle-outline" size="small" class="me-1" />
          수정하기
        </v-btn>
      </CCol>
      <CCol xs="auto">
        <v-btn type="button" color="primary" @click="toCreate">
          <v-icon icon="mdi-check-circle-outline" size="small" class="me-1" />
          등록하기
        </v-btn>
      </CCol>
    </CRow>
  </CCardFooter>

  <AlertModal ref="refAlertModal" />
</template>
