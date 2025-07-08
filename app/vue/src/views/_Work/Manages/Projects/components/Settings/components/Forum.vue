<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { useRoute } from 'vue-router'
import { isValidate } from '@/utils/helper.ts'
import { useBoard } from '@/store/pinia/board.ts'
import type { Board } from '@/store/types/board.ts'
import draggable from 'vuedraggable'
import NoData from '@/views/_Work/components/NoData.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({ project: { type: Number, required: true } })

const route = useRoute()

const RefForumForm = ref()

const validated = ref(false)
const form = ref<Board>({
  pk: null as number | null,
  project: null as number | null,
  name: '',
  description: '',
  parent: null as number | null,
})

const brdStore = useBoard()
const boardList = computed(() => brdStore.boardList)
const fetchBoardList = (payload: any) => brdStore.fetchBoardList(payload)

const onSubmit = (event: Event) => {
  if (isValidate(event)) validated.value = true
  else {
    brdStore.createBoard({ ...form.value })
    validated.value = false
    form.value.pk = null
    form.value.name = ''
    form.value.description = ''
    form.value.parent = null
    RefForumForm.value.close()
  }
}

const projId = computed(() => route.params.projId as string)

watch(projId, nVal => {
  if (nVal) fetchBoardList({ project: nVal })
})

onBeforeMount(() => {
  fetchBoardList({ project: projId.value })
  form.value.project = props.project as number
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1" @click="RefForumForm.callModal()">새 게시판</router-link>
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
            <CTableHeaderCell class="pl-2" colspan="3">게시판</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="brd in boardList" :key="brd.pk">
            <CTableDataCell class="pl-2">
              <router-link to="">{{ brd.name }}</router-link>
            </CTableDataCell>
            <CTableDataCell>{{ brd.description }}</CTableDataCell>
            <CTableDataCell>
              <v-icon
                icon="mdi-arrow-up-down-bold"
                color="success"
                size="16"
                class="cursor-move mr-3"
              />
              <span class="mr-3 cursor-pointer">
                <v-icon icon="mdi-pencil" color="amber" size="15" class="mr-2" />
                <router-link to="">편집</router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can-outline" color="grey" size="15" class="mr-2" />
                <router-link to="">삭제</router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
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
            <CFormLabel for="description" class="col-sm-3 col-form-label required">
              설명
            </CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.description"
                id="description"
                maxlength="255"
                required
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
</template>
