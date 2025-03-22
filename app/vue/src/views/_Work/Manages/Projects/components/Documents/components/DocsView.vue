<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, type PropType, ref } from 'vue'
import type { Docs } from '@/store/types/docs'
import { useDocs } from '@/store/pinia/docs'
import { useRoute, useRouter } from 'vue-router'
import { timeFormat } from '@/utils/baseMixins'
import PostInfo from '@/components/OtherParts/PostInfo.vue'
import PostContent from '@/components/OtherParts/PostContent.vue'
import PostedFile from '@/components/OtherParts/PostedFile.vue'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, required: true },
  heatedPage: { type: Array as PropType<number[]>, default: () => [] },
})

const emit = defineEmits(['docs-hit'])

const docStore = useDocs()
const [route, router] = [useRoute(), useRouter()]

const docId = computed(() => Number(route.params.docId))

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
          <v-icon icon="mdi-pencil" color="warning" size="sm" />
          <router-link :to="{ name: '(문서) - 편집' }" class="ml-1">편집</router-link>
        </span>

        <span class="mr-2 form-text">
          <v-icon icon="mdi-trash-can-outline" color="secondary" size="sm" />
          <router-link :to="{ name: '(문서) - 삭제' }" class="ml-1">삭제</router-link>
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

    <CRow>
      <CCol>
        <CRow>
          <CCol><h5>파일</h5></CCol>
        </CRow>

        <PostedFile :docs="docs.pk as number" :files="docs.files" />
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="mt-4">
      <CCol class="text-right">
        <CButton color="light" @click="router.replace({ name: '(문서)' })" size="sm">
          목록으로
        </CButton>
      </CCol>
    </CRow>
  </div>
</template>
