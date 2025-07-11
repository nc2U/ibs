<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBoard } from '@/store/pinia/board.ts'
import type { Board } from '@/store/types/board.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const brdStore = useBoard()
const boardList = computed(() => brdStore.boardList)
const fetchBoardList = (payload: any) => brdStore.fetchBoardList(payload)

// 2. 정렬본 목록
const STORAGE_KEY = 'boardList'
const orderedList = ref<Board[]>([])

const route = useRoute()
watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) console.log(nVal)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  await fetchBoardList({ project: route.params.projId })
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ route.name }}</h5>
        </CCol>
      </CRow>
      {{ boardList }}
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
