<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useForum } from '@/store/pinia/forum'
import type { Forum } from '@/store/types/forum'
import { useRoute } from 'vue-router'
import { getOrderedList, isValidate, setLocalStorage } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import Draggable from 'vuedraggable'
import NoData from '@/components/NoData/Index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({ project: { type: Number, required: true } })

const route = useRoute()

const RefForumForm = ref<InstanceType<typeof FormModal> | null>(null)
const RefDelConfirm = ref<InstanceType<typeof ConfirmModal> | null>(null)

const { can, PERM } = usePerms()
const canForumManage = computed(() => can(PERM.FORUM_MANAGE, route.params.projId as string))

const validated = ref(false)
const form = ref<Forum>({
  pk: null as number | null,
  project: null as number | null,
  name: '',
  description: '',
  parent: null as number | null,
})

const resetForm = () => {
  form.value.pk = null
  form.value.project = props.project
  form.value.name = ''
  form.value.description = ''
  form.value.parent = null
}

const frmStore = useForum()
// 1. 원본 목록
const forumList = computed(() => frmStore.forumList as Forum[])
const fetchForumList = (payload: Parameters<typeof frmStore.fetchForumList>[0]) =>
  frmStore.fetchForumList(payload)

// 상위 게시판 선택 시 본인 및 하위 게시판 제외 (순환 참조 방지)
const availableParentForums = computed(() => {
  if (!form.value.pk) return forumList.value
  const excluded = new Set<number>([form.value.pk])
  let added = true
  while (added) {
    added = false
    for (const f of forumList.value) {
      if (f.pk && f.parent && excluded.has(f.parent) && !excluded.has(f.pk)) {
        excluded.add(f.pk)
        added = true
      }
    }
  }
  return forumList.value.filter(f => !f.pk || !excluded.has(f.pk))
})

watch(
  () => props.project,
  nVal => {
    if (nVal && !form.value.pk) {
      form.value.project = nVal
    }
  },
  { immediate: true },
)

// 프로젝트 변경 시 목록 다시 불러오기
const projId = computed(() => route.params.projId as string)
watch(projId, async nVal => {
  if (nVal) {
    await fetchForumList({ project: nVal })
    form.value.project = props.project as number
  }
})

// 2. 정렬본 목록 (워크스페이스별 키 격리)
const storageKey = computed(() => `forumList_${projId.value || props.project}`)
const orderedList = ref<Forum[]>([])

// 원본 목록 변경 시 정렬본 다시 불러오기
watch(
  [forumList, storageKey],
  ([nVal, key]) => {
    orderedList.value = getOrderedList(
      nVal.filter((f): f is Forum & { pk: number } => typeof f.pk === 'number'),
      key,
    )
  },
  { immediate: true },
)

const saveForumOrder = () => {
  setLocalStorage(
    orderedList.value.filter((f): f is Forum & { pk: number } => typeof f.pk === 'number'),
    storageKey.value,
  )
}

// 게시판 등록 수정
const createForum = () => {
  validated.value = false
  resetForm()
  RefForumForm.value?.callModal()
}

const modifyCall = (frm: Forum) => {
  validated.value = false
  form.value.pk = frm.pk
  form.value.project = frm.project
  form.value.name = frm.name
  form.value.description = frm.description
  form.value.parent = frm.parent
  RefForumForm.value?.callModal()
}

const onSubmit = async (event: Event) => {
  if (isValidate(event)) validated.value = true
  else {
    const rawParent = form.value.parent as number | string | null
    const parentVal = rawParent === '' || rawParent === null ? null : Number(rawParent)
    const payload = {
      ...form.value,
      project: form.value.project ?? props.project,
      parent: Number.isNaN(parentVal) ? null : parentVal,
    }
    let result: unknown = null
    if (form.value.pk) {
      const { pk, ...rest } = payload
      result = await frmStore.updateForum(pk as number, rest, projId.value)
    } else {
      result = await frmStore.createForum(payload, projId.value)
    }
    if (!result) return
    validated.value = false
    RefForumForm.value?.close()
    resetForm()
  }
}

// 게시판 삭제 로직
const delForumPk = ref<number | null>(null)
const deleteModalCall = (pk: number) => {
  delForumPk.value = pk
  RefDelConfirm.value?.callModal()
}
const deleteForum = async () => {
  if (delForumPk.value) {
    const ok = await frmStore.deleteForum(delForumPk.value, route.params.projId as string)
    if (ok) RefDelConfirm.value?.close()
  }
}

onBeforeMount(async () => {
  form.value.project = props.project as number
  await fetchForumList({ project: projId.value })
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span v-if="canForumManage">
        <TextButton name="새 게시판" @click="createForum" />
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!forumList.length" />

  <CRow v-else>
    <CCol class="mt-3">
      <CTable table small hover responsive>
        <colgroup>
          <col style="width: 30%" />
          <col style="width: 45%" />
          <col style="width: 25%" />
        </colgroup>
        <CTableHead>
          <CTableRow color="secondary">
            <CTableHeaderCell class="ps-3" colspan="3">게시판</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <Draggable v-model="orderedList" tag="tbody" item-key="pk" @end="saveForumOrder">
          <template #item="{ element }">
            <CTableRow>
              <CTableDataCell class="ps-3">
                <router-link
                  :to="{
                    name: '(게시판) - 보기',
                    params: { projId: route.params.projId, forumId: element.pk },
                  }"
                >
                  {{ element.name }}
                </router-link>
              </CTableDataCell>
              <CTableDataCell>{{ element.description }}</CTableDataCell>
              <CTableDataCell>
                <v-icon
                  icon="mdi-arrow-up-down-bold"
                  color="success"
                  size="16"
                  class="cursor-move me-3"
                />
                <span v-if="canForumManage" class="me-3 cursor-pointer">
                  <v-icon icon="mdi-pencil" color="amber" size="15" class="me-2" />
                  <a href="#" @click.prevent="modifyCall(element)">편집</a>
                </span>
                <span v-if="canForumManage">
                  <v-icon icon="mdi-trash-can-outline" color="grey" size="15" class="me-2" />
                  <a href="#" @click.prevent="deleteModalCall(element.pk)">삭제</a>
                </span>
              </CTableDataCell>
            </CTableRow>
          </template>
        </Draggable>
      </CTable>
    </CCol>
  </CRow>

  <FormModal ref="RefForumForm">
    <template #header><span v-if="!form.pk">새</span> 게시판</template>
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
          <CRow v-if="availableParentForums.length" class="mb-3">
            <CFormLabel for="parent" class="col-sm-3 col-form-label">상위 게시판</CFormLabel>
            <CCol sm="9">
              <CFormSelect v-model="form.parent" id="parent">
                <option value="">---------</option>
                <option
                  v-for="frm in availableParentForums"
                  :value="frm.pk"
                  :key="frm.pk as number"
                >
                  {{ frm.name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn
            type="submit"
            :color="form.pk ? 'success' : 'primary'"
            size="small"
            :disabled="!canForumManage"
          >
            확인
          </v-btn>
          <v-btn color="grey" variant="tonal" size="small" @click="RefForumForm?.close()">
            닫기
          </v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="RefDelConfirm">
    <template #header>게시판 삭제</template>
    <template #default>
      이 게시판을 삭제하면 해당 게시물 등 관련된 데이터가 전부 삭제됩니다.<br />
      계속 진행 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" :disabled="!canForumManage" @click="deleteForum">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>
</template>
