<script lang="ts" setup>
import { ref, computed, type PropType, onBeforeMount, onUpdated, nextTick } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import type { Board } from '@/store/types/board'
import { useProject } from '@/store/pinia/project'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  nowBoard: { type: Number, default: null },
  nowProject: { type: Number, default: null },
  boardList: { type: Array as PropType<Board[]>, default: () => [] },
  isCopy: { type: Boolean, default: false },
})

const emit = defineEmits(['copy-post', 'move-post'])

const refListModal = ref()

const board = ref<number | null>(null)
const project = ref<number | null>(null)

const projStore = useProject()
const projSelectList = computed(() => projStore.projSelect)

const formCheck = computed(() => {
  const a = board.value == props.nowBoard
  const b = project.value == props.nowProject
  return a && b
})

const brdChk = () =>
  nextTick(() => (board.value === 1 ? (project.value = null) : (project.value = props.nowProject)))

const onSubmit = () => {
  if (props.isCopy) emit('copy-post', board.value, project.value ?? undefined)
  else emit('move-post', board.value, project.value ?? undefined)
  refListModal.value.close()
}

const callModal = () => refListModal.value.callModal()

defineExpose({ callModal })

onBeforeMount(() => {
  if (props.nowProject) project.value = props.nowProject
})

onUpdated(() => {
  if (props.nowBoard) board.value = props.nowBoard
  if (props.nowProject) project.value = props.nowProject
})
</script>

<template>
  <AlertModal ref="refListModal" size="lg">
    <template #header> 게시물 {{ isCopy ? '복사' : '이동' }}</template>
    <template #default>
      <CRow class="mb-3">
        <CFormLabel for="staticEmail" class="col-sm-3 col-form-label pl-5">
          본사 / 프로젝트 선택
        </CFormLabel>
        <div class="col-sm-9">
          <CFormSelect v-model="project" :disabled="board === 1">
            <option value="">본사 게시물</option>
            <option v-for="p in projSelectList" :value="p.value" :key="p.value">
              {{ p.label }}
            </option>
          </CFormSelect>
        </div>
      </CRow>
      <CTable v-if="boardList.length" striped class="mt-3 border-top-1">
        <colgroup>
          <col style="width: 80%" />
          <col style="width: 20%" />
        </colgroup>
        <CTableBody>
          <CTableRow v-for="obj in boardList" :key="obj.pk" :item-key="obj.pk">
            <CTableDataCell>
              <div class="form-check">
                <input
                  v-model="board"
                  :id="`board_${obj.pk}`"
                  :value="obj.pk"
                  type="radio"
                  class="form-check-input"
                  style="margin-top: 6px"
                  :disabled="nowBoard === obj.pk"
                />
                <!--                  @change="brdChk"-->
                <label :for="`board_${obj.pk}`" class="form-label form-check-label">
                  {{ obj.name }}
                </label>
              </div>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge v-if="nowBoard === obj.pk" color="warning">현재</CBadge>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CRow v-else class="text-center">
        <CCol class="py-5">등록된 게시판이 없습니다.</CCol>
      </CRow>
    </template>
    <template #footer>
      <v-btn
        :color="isCopy ? 'info' : 'warning'"
        size="small"
        @click="onSubmit"
        :disabled="formCheck"
      >
        게시물 {{ isCopy ? '복사' : '이동' }}
      </v-btn>
      <v-btn :color="btnLight" size="small" @click="refListModal.close()">닫기</v-btn>
    </template>
  </AlertModal>
</template>
