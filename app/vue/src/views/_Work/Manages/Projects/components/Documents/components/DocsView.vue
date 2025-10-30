<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, type PropType, ref } from 'vue'
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
  <div v-if="docs">
    <CRow class="pt-3">
      <CCol>
        <h5>{{ docs.title }}</h5>
      </CCol>

      <CCol class="text-right">
        <span class="mr-2 form-text">
          <v-icon icon="mdi-pencil" color="warning" size="15" class="mr-1" />
          <router-link :to="{ name: '(문서) - 편집' }" class="ml-1">편집</router-link>
        </span>

        <span class="mr-2 form-text">
          <v-icon icon="mdi-trash-can-outline" color="secondary" size="15" class="mr-1" />
          <router-link to="#" @click.prevent="refConfirmModal.callModal()" class="ml-1"
            >삭제</router-link
          >
        </span>
      </CCol>
    </CRow>

    <CRow class="text-grey">
      <CCol>
        {{ docs.proj_name }} ➤ {{ docs.cate_name }} ➤ ({{
          timeFormat(docs.created as string, true, '/')
        }})
      </CCol>
    </CRow>

    <v-divider />

    <PostInfo :docs="docs" />

    <PostContent :content="docs.content" />

    <CRow class="mb-3">
      <CCol>
        <CRow v-if="docs.files?.length">
          <CCol><h5>파일</h5></CCol>
        </CRow>

        <PostedFile :docs="docs.pk as number" :files="docs.files" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol>
        <CRow v-if="docs.links?.length">
          <CCol><h5>링크</h5></CCol>
        </CRow>

        <PostedLink :docs="docs.pk as number" :links="docs.links" />
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="mt-4">
      <CCol class="text-right">
        <v-btn :color="btnLight" @click="router.replace({ name: '(문서)' })" size="small">
          목록으로
        </v-btn>
      </CCol>
    </CRow>
  </div>

  <ConfirmModal ref="refConfirmModal">
    <template #header>알림!</template>
    <template #default> 이 문서를 삭제 합니다. 계속 진행 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>
</template>
