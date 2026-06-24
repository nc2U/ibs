<script lang="ts" setup>
import { computed, inject, onBeforeMount, onMounted, type PropType, ref } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import type { Docs } from '@/store/types/docs'
import { useDocs } from '@/store/pinia/docs'
import { useRoute, useRouter } from 'vue-router'
import { timeFormat } from '@/utils/baseMixins'
import PostInfo from '@/components/OtherParts/PostInfo.vue'
import PostContent from '@/components/OtherParts/PostContent.vue'
import PostedFile from '@/components/OtherParts/PostedFile.vue'
import PostedLink from '@/components/OtherParts/PostedLink.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, required: true },
  heatedPage: { type: Array as PropType<number[]>, default: () => [] },
})

const emit = defineEmits(['docs-hit'])

const refConfirmModal = ref()

const docStore = useDocs()
const [route, router] = [useRoute(), useRouter()]

const userInfo = inject<any>('userInfo')

const docId = computed(() => Number(route.params.docId))

const modalAction = () => {
  docStore.deleteDocs(props.docs.pk as number, {})
  refConfirmModal.value.close()
  router.push({ name: '(문서)' })
}

onBeforeMount(() => {
  if (docId.value) {
    docStore.fetchDocs(docId.value)
  }
})

onMounted(() => {
  if (docId.value && !props.heatedPage?.includes(docId.value)) {
    emit('docs-hit', docId.value)
  }
})
</script>

<template>
  <div v-if="docs" class="pa-4">
    <CRow class="mb-2">
      <CCol>
        <h4 class="font-weight-bold mb-1">{{ docs.title }}</h4>
      </CCol>
    </CRow>

    <CRow class="text-grey text-caption mb-3">
      <CCol>
        <span>{{ docs.proj_name }}</span>
        <v-icon icon="mdi-chevron-right" size="small" class="mx-1" />
        <span>{{ docs.cate_name }}</span>
        <v-icon icon="mdi-calendar-range" size="small" class="ml-3 mr-1" />
        <span>{{ timeFormat(docs.created as string, 'short', '/') }}</span>
      </CCol>
    </CRow>

    <v-divider class="mb-3" />

    <PostInfo :docs="docs" class="mb-4" />

    <PostContent :description="docs.description" class="mb-5" />

    <div class="files-section">
      <CRow class="mb-3 pt-4">
        <CCol>
          <h6 class="mb-2">첨부 파일</h6>
          <PostedFile :docs="docs.pk as number" :files="docs.files" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol>
          <h6 class="mb-2">관련 링크</h6>
          <PostedLink :docs="docs.pk as number" :links="docs.links" />
        </CCol>
      </CRow>
    </div>

    <v-divider class="mb-3" />

    <CRow class="mt-4">
      <CCol class="text-right">
        <v-btn
          :color="btnLight"
          @click="router.replace({ name: '(문서)' })"
          size="small"
          class="mr-2"
        >
          목록으로
        </v-btn>

        <v-btn
          v-if="userInfo.is_superuser || userInfo.pk === docs.creator?.pk"
          color="success"
          size="small"
          class="mr-2"
          :to="{ name: '(문서) - 편집' }"
        >
          <v-icon icon="mdi-pencil" size="small" class="mr-1" />
          편집
        </v-btn>

        <v-btn
          v-if="userInfo.is_superuser || userInfo.pk === docs.creator?.pk"
          color="warning"
          size="small"
          @click.prevent="refConfirmModal.callModal()"
        >
          <v-icon icon="mdi-trash-can-outline" size="small" class="mr-1" />
          삭제
        </v-btn>
      </CCol>
    </CRow>
  </div>

  <ConfirmModal ref="refConfirmModal">
    <template #header>알림!</template>
    <template #default> 이 문서를 삭제 합니다. 계속 진행 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
