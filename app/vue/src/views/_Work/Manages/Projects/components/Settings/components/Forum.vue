<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { useRoute } from 'vue-router'
import { isValidate } from '@/utils/helper.ts'
import { useBoard } from '@/store/pinia/board.ts'
import type { Board } from '@/store/types/board.ts'
import { getOrderedList, setLocalStorage } from '@/utils/helper.ts'
import Draggable from 'vuedraggable'
import NoData from '@/views/_Work/components/NoData.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({ project: { type: Number, required: true } })

const route = useRoute()

const RefForumForm = ref()
const RefDelConfirm = ref()

const validated = ref(false)
const form = ref<Board>({
  pk: null as number | null,
  project: null as number | null,
  name: '',
  description: '',
  parent: null as number | null,
})

const resetForm = () => {
  form.value.pk = null
  form.value.name = ''
  form.value.description = ''
  form.value.parent = null
}

const brdStore = useBoard()
// 1. 원본 목록
const boardList = computed(() => brdStore.boardList as Board[])
const fetchBoardList = (payload: any) => brdStore.fetchBoardList(payload)

// 프로젝트 변경 시 목록 다시 불러오기
const projId = computed(() => route.params.projId as string)
watch(projId, nVal => {
  if (nVal) fetchBoardList({ project: nVal })
})

// 2. 정렬본 목록
const orderedList = ref<Board[]>([])
const STORAGE_KEY = 'boardList'

// 원본 목록 변경 시 정렬본 다시 불러오기
watch(
  boardList,
  nVal => {
    orderedList.value = getOrderedList(nVal as any[], STORAGE_KEY)
  },
  { immediate: true },
)

// 게시판 등록 수정
const crateBoard = () => {
  resetForm()
  RefForumForm.value.callModal()
}

const modifyCall = (brd: Board) => {
  form.value.pk = brd.pk
  form.value.project = brd.project
  form.value.name = brd.name
  form.value.description = brd.description
  form.value.parent = brd.parent
  RefForumForm.value.callModal()
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) validated.value = true
  else {
    if (form.value.pk) {
      const { pk, ...rest } = form.value
      brdStore.updateBoard(pk as number, rest)
    } else brdStore.createBoard({ ...form.value })
    validated.value = false
    RefForumForm.value.close()
    resetForm()
  }
}

// 게시판 삭제 로직
const delBoardPk = ref<number | null>(null)
const deleteModalCall = (pk: number) => {
  delBoardPk.value = pk
  RefDelConfirm.value.callModal()
}
const deleteBoard = () => {
  brdStore.deleteBoard(delBoardPk.value as number, route.params.projId as string)
  RefDelConfirm.value.close()
}

onBeforeMount(async () => {
  form.value.project = props.project as number
  await fetchBoardList({ project: projId.value })
  if (boardList.value.length)
    orderedList.value = getOrderedList(boardList.value as any[], STORAGE_KEY)
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1" @click="crateBoard">새 게시판</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!boardList.length" />

  <CRow v-else>
    <CCol class="mt-3">
      <CTable table small hover responsive>
        <col style="width: 30%" />
        <col style="width: 45%" />
        <col style="width: 25%" />
        <CTableHead>
          <CTableRow color="secondary">
            <CTableHeaderCell class="pl-3" colspan="3">게시판</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <Draggable
          v-model="orderedList"
          tag="tbody"
          item-key="name"
          @end="setLocalStorage(orderedList as any[], STORAGE_KEY)"
        >
          <template #item="{ element }">
            <CTableRow class="asdfasdf">
              <CTableDataCell class="pl-3">
                <router-link to="">{{ element.name }}</router-link>
              </CTableDataCell>
              <CTableDataCell>{{ element.description }}</CTableDataCell>
              <CTableDataCell>
                <v-icon
                  icon="mdi-arrow-up-down-bold"
                  color="success"
                  size="16"
                  class="cursor-move mr-3"
                />
                <span class="mr-3 cursor-pointer">
                  <v-icon icon="mdi-pencil" color="amber" size="15" class="mr-2" />
                  <router-link to="" @click="modifyCall(element)">편집</router-link>
                </span>
                <span>
                  <v-icon icon="mdi-trash-can-outline" color="grey" size="15" class="mr-2" />
                  <router-link to="" @click="deleteModalCall(element.pk)">삭제</router-link>
                </span>
              </CTableDataCell>
            </CTableRow>
          </template>
        </Draggable>
      </CTable>
    </CCol>
  </CRow>

  <FormModal ref="RefForumForm">
    <template #header>새 게시판</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CModalBody class="text-body">
          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-3 col-form-label required">이름</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.name"
                id="name"
                placeholder="게시판 이름"
                maxlength="255"
                required
              />
            </CCol>
          </CRow>
          <CRow class="mb-3 required">
            <CFormLabel for="description" class="col-sm-3 col-form-label"> 설명</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.description"
                id="description"
                maxlength="255"
                placeholder="게시판에 대한 설명"
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="parent" class="col-sm-3 col-form-label">상위 게시판</CFormLabel>
            <CCol sm="9">
              <CFormSelect v-model="form.parent" id="parent">
                <option value="">---------</option>
                <option v-for="brd in boardList" :value="brd.pk" :key="brd.pk as number">
                  {{ brd.name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" size="small" @click="RefForumForm.close()"> 닫기</v-btn>
          <v-btn type="submit" color="primary" size="small">확인</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="RefDelConfirm">
    <template #default>
      이 게시판을 삭제하면 해당 게시물 등 관련된 데이터가 전부 삭제됩니다.<br />
      계속 진행 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteBoard">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
