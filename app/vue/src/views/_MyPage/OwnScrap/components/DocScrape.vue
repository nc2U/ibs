<script setup lang="ts">
import { ref, computed, type PropType, onBeforeMount } from 'vue'
import type { Scrape as S } from '@/store/types/accounts'
import { cutString, timeFormat } from '@/utils/baseMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  scrape: { type: Object as PropType<S>, default: null },
})

const emit = defineEmits(['patch-title', 'del-scrape'])

const refConfirmModal = ref()
const titleEdit = ref(false)
const scrapeTitle = ref('')

const viewRoute = computed(() => {
  if (props.scrape?.docs?.proj_sort === '1') {
    // 본사관리
    if (props.scrape?.docs?.doc_type === 1) return '본사 일반 문서'
    else if (props.scrape?.docs?.doc_type === 2) return '본사 소송 문서'
  } else if (props.scrape.docs?.proj_sort === '2') {
    // 부동산개발 프로젝트
    if (props.scrape.docs?.doc_type === 1) return '현장 일반 문서'
    else if (props.scrape.docs?.doc_type === 2) return '현장 소송 문서'
  }
})

const patchTitle = () => {
  emit('patch-title', props.scrape.pk, scrapeTitle.value)
  titleEdit.value = false
}

const delScrape = () => refConfirmModal.value.callModal('', '', '', 'warning')

const modalAction = () => emit('del-scrape', props.scrape.pk)

onBeforeMount(() => {
  if (props.scrape?.title) scrapeTitle.value = props.scrape.title
})
</script>

<template>
  <CTableRow v-if="scrape" class="text-center">
    <CTableDataCell>{{ scrape.docs?.pk }}</CTableDataCell>
    <CTableDataCell>
      <router-link :to="{ name: viewRoute }">{{ viewRoute }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="!titleEdit">
        <router-link :to="{ name: `${viewRoute} - 보기`, params: { docsId: scrape.docs?.pk } }">
          {{ cutString(scrape.title || scrape.docs?.title, 50) }}
        </router-link>
      </span>
      <span v-else>
        <CInputGroup>
          <CFormInput
            v-model="scrapeTitle"
            placeholder="스크랩 제목을 입력하세요"
            aria-label="Alias title"
            :aria-describedby="`alias-title-${scrape.pk}`"
            @keydown.enter="patchTitle"
          />
          <CButton @click="patchTitle" type="button" color="info" :id="`alias-title-${scrape.pk}`">
            저장
          </CButton>
        </CInputGroup>
      </span>
    </CTableDataCell>
    <CTableDataCell>{{ timeFormat(scrape.created ?? '') }}</CTableDataCell>
    <CTableDataCell>
      <v-btn
        @click="titleEdit = !titleEdit"
        density="compact"
        icon="mdi-plus"
        rounded="1"
        size="sm"
        color="success"
      />
    </CTableDataCell>
    <CTableDataCell>
      <v-btn
        @click="delScrape"
        density="compact"
        icon="mdi-trash-can-outline"
        size="sm"
        rounded="1"
        color="red"
      />
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 스크랩 정보 삭제</template>
    <template #default> 삭제 후 복구할 수 없습니다. 스크랩 삭제를 진행하시겠습니까?</template>
    <template #footer>
      <CButton color="danger" @click="modalAction"> 삭제</CButton>
    </template>
  </ConfirmModal>
</template>
