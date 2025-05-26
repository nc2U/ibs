<script lang="ts" setup>
import { ref, type PropType, nextTick } from 'vue'
import type { Version } from '@/store/types/work_project.ts'
import { colorLight } from '@/utils/cssMixins'
import NoData from '@/views/_Work/components/NoData.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ versions: { type: Array as PropType<Version[]>, default: () => [] } })

const emit = defineEmits(['version-filter', 'delete-version'])

const RefVersionConfirm = ref()

const status = ref('1')
const search = ref('')

const deleteVersion = ref<number | null>(null)

const textClass = ['text-primary', 'text-warning', 'text-secondary']

const versionFilter = () => {
  nextTick(() => emit('version-filter', { status: status.value, search: search.value }))
}
const formReset = () => {
  status.value = '1'
  search.value = ''
  emit('version-filter', { status: status.value, search: search.value })
}

const toDelete = (ver: number) => {
  deleteVersion.value = ver
  RefVersionConfirm.value.callModal('', '이 버전 삭제를 계속 진행 하시겠습니까?', '', 'warning')
}

const deleteSubmit = () => {
  emit('delete-version', deleteVersion.value)
  RefVersionConfirm.value.close()
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: '(로드맵) - 추가', query: { back: 1 } }" class="ml-1">
          새 버전
        </router-link>
      </span>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-lock" color="warning" size="sm" />
        <router-link to="" class="ml-1">완료된 버전 닫기 </router-link>
      </span>
    </CCol>
  </CRow>

  <CRow class="mt-3">
    <CCol>
      <h6>
        <v-icon icon="mdi-check" color="success" size="sm" />
        검색조건
      </h6>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CCard class="mb-3" :color="colorLight">
        <CCardBody>
          <CRow>
            <CFormLabel for="inputEmail3" class="col-sm-1 col-form-label text-right">
              상태
            </CFormLabel>
            <CCol sm="2">
              <CFormSelect v-model="status" @change="versionFilter">
                <option value="">모두</option>
                <option value="1">진행</option>
                <option value="2">잠김</option>
                <option value="3">닫힘</option>
              </CFormSelect>
            </CCol>

            <CFormLabel for="inputEmail3" class="col-sm-1 col-form-label text-right">
              버전
            </CFormLabel>
            <CCol sm="2">
              <CFormInput v-model="search" placeholder="검색어 입력" />
            </CCol>

            <CCol class="pt-1">
              <v-btn color="primary" size="small" variant="outlined" @click="versionFilter">
                적용
              </v-btn>
              <span class="ml-2">
                <v-icon icon="mdi-reload" size="sm" color="success" />
                <router-link to="" @click="formReset">지우기</router-link>
              </span>
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <NoData v-if="!versions.length" />

  <CRow v-else>
    <CCol>
      <v-divider class="my-0" />
      <CTable small striped responsive hover>
        <colgroup>
          <col style="width: 10%" />
          <col style="width: 5%" />
          <col style="width: 15%" />
          <col style="width: 20%" />
          <col style="width: 5%" />
          <col style="width: 15%" />
          <col style="width: 20%" />
          <col style="width: 10%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>버전</CTableHeaderCell>
            <CTableHeaderCell>기본 버전</CTableHeaderCell>
            <CTableHeaderCell>날짜</CTableHeaderCell>
            <CTableHeaderCell>설명</CTableHeaderCell>
            <CTableHeaderCell>상태</CTableHeaderCell>
            <CTableHeaderCell>공유</CTableHeaderCell>
            <CTableHeaderCell>위키 페이지</CTableHeaderCell>
            <CTableHeaderCell></CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="ver in versions" :key="ver.pk" class="text-center">
            <CTableDataCell
              class="text-left pl-4"
              :class="{ 'text-secondary': ver.status === '3' }"
            >
              {{ ver.name }}
            </CTableDataCell>
            <CTableDataCell :class="{ 'text-secondary': ver.status === '3' }">
              <v-icon v-if="ver.is_default" icon="mdi-check-bold" color="success" size="sm" />
            </CTableDataCell>
            <CTableDataCell :class="{ 'text-secondary': ver.status === '3' }">
              {{ ver.effective_date }}
            </CTableDataCell>
            <CTableDataCell class="text-left" :class="{ 'text-secondary': ver.status === '3' }">
              {{ ver.description }}
            </CTableDataCell>
            <CTableDataCell :class="textClass[Number(ver.status) - 1]">
              {{ ver.status_desc }}
            </CTableDataCell>
            <CTableDataCell :class="{ 'text-secondary': ver.status === '3' }">
              {{ ver.sharing_desc }}
            </CTableDataCell>
            <CTableDataCell class="text-left" :class="{ 'text-secondary': ver.status === '3' }">
              <router-link
                v-if="ver.wiki_page_title"
                :to="{ name: '(위키) - 제목', params: { title: ver.wiki_page_title } }"
              >
                {{ ver.wiki_page_title }}
              </router-link>
            </CTableDataCell>
            <CTableDataCell class="form-text">
              <span class="mr-2">
                <v-icon icon="mdi-pencil" color="amber" size="sm" class="mr-1" />
                <router-link
                  :to="{ name: '(로드맵) - 수정', params: { verId: ver.pk }, query: { back: 1 } }"
                >
                  편집
                </router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can" color="grey" size="sm" class="mr-1" />
                <router-link to="" @click="toDelete(ver?.pk as number)">삭제</router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <ConfirmModal ref="RefVersionConfirm">
    <template #footer>
      <v-btn color="warning" @click="deleteSubmit">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
