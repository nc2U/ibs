<script lang="ts" setup>
import { ref, type PropType, nextTick, computed } from 'vue' // computed 추가
import { usePerms } from '@/composables/usePerms' // 추가
import { colorLight } from '@/utils/cssMixins'
import type { Version } from '@/store/types/work_project.ts'
import NoData from '@/components/NoData/Index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '../../../../../components/atomics/TextButton.vue'

defineProps({
  versions: { type: Array as PropType<Version[]>, default: () => [] },
  currentProjectSlug: { type: String, required: true },
})

const emit = defineEmits(['version-filter', 'delete-version'])

// 권한 설정 추가
const { can, PERM } = usePerms()
const canManageVersions = computed(() => can(PERM.PROJECT_VERSION))

const RefVersionConfirm = ref()

const status = ref('')
const search = ref('')

const deleteVersion = ref<number | null>(null)

const textClass = ['text-primary', 'text-warning', 'text-secondary']

const versionFilter = () => {
  nextTick(() => emit('version-filter', { status: status.value, search: search.value }))
}
const formReset = () => {
  status.value = ''
  search.value = ''
  emit('version-filter', { status: status.value, search: search.value })
}

const toDelete = (ver: number) => {
  deleteVersion.value = ver
  RefVersionConfirm.value.callModal('', '이 단계 삭제를 계속 진행 하시겠습니까?', '', 'warning')
}

const deleteSubmit = () => {
  emit('delete-version', deleteVersion.value)
  RefVersionConfirm.value.close()
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span v-if="canManageVersions" class="mr-2 form-text">
        <TextButton name="새 단계" :to="{ name: '(로드맵) - 추가', query: { back: 1 } }" />
      </span>
    </CCol>

    <CCol class="text-right">
      <span v-if="canManageVersions" class="mr-2 form-text">
        <TextButton
          name="완료된 단계 닫기"
          icon="mdi-lock"
          icon-color="warning"
          color="secondary"
        />
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
              단계
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
          <col style="width: 15%" />
          <col style="width: 10%" />
          <col style="width: 15%" />
          <col style="width: 20%" />
          <col style="width: 10%" />
          <col style="width: 20%" />
          <col style="width: 10%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>단계</CTableHeaderCell>
            <CTableHeaderCell>기본 단계</CTableHeaderCell>
            <CTableHeaderCell>날짜</CTableHeaderCell>
            <CTableHeaderCell>설명</CTableHeaderCell>
            <CTableHeaderCell>상태</CTableHeaderCell>
            <CTableHeaderCell>공유</CTableHeaderCell>
            <CTableHeaderCell></CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="ver in versions" :key="ver.pk" class="text-center">
            <CTableDataCell
              class="text-left pl-4"
              :class="{ 'text-secondary': ver.status === '3' }"
            >
              <template v-if="ver.project?.slug !== currentProjectSlug">
                <v-icon icon="mdi-link-variant" color="grey" size="sm" class="mr-2" />

                <router-link
                  :to="{
                    name: '(로드맵) - 보기',
                    params: { projId: ver.project?.slug, verId: ver.pk },
                  }"
                >
                  <small class="text-muted">[{{ ver.project?.name }}] </small>
                  {{ ver.name }}
                </router-link>
              </template>
              <template v-else>
                <router-link
                  :to="{
                    name: '(로드맵) - 보기',
                    params: { projId: ver.project?.slug, verId: ver.pk },
                  }"
                  class="pl-4"
                >
                  {{ ver.name }}
                </router-link>
              </template>
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
            <CTableDataCell class="form-text">
              <span v-if="ver.project?.slug === currentProjectSlug">
                <span v-if="canManageVersions" class="mr-2">
                  <v-icon icon="mdi-pencil" color="amber" size="sm" class="mr-1" />
                  <router-link
                    :to="{ name: '(로드맵) - 수정', params: { verId: ver.pk }, query: { back: 1 } }"
                  >
                    편집
                  </router-link>
                </span>
                <span v-if="canManageVersions">
                  <v-icon icon="mdi-trash-can" color="grey" size="sm" class="mr-1" />
                  <router-link to="" @click="toDelete(ver?.pk as number)">삭제</router-link>
                </span>
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
