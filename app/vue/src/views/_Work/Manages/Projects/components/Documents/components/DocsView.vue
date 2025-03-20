<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'
import { useDocs } from '@/store/pinia/docs'
import { useRoute, useRouter } from 'vue-router'
import { timeFormat } from '@/utils/baseMixins'
import sanitizeHtml from 'sanitize-html'
import PostedFile from '@/components/OtherParts/PostedFile.vue'
import PostedLink from '@/components/OtherParts/PostedLink.vue'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, required: true },
  heatedPage: { type: Array as PropType<number[]>, default: () => [] },
})

const emit = defineEmits(['docs-hit'])

const docStore = useDocs()
const [route, router] = [useRoute(), useRouter()]

const docId = computed(() => Number(route.params.docId))

// file 관련 코드
const fileDelete = (payload: FormData) => alert('준비중입니다!') // del_file 전달 파일 삭제 patch 실행

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
    <CRow class="py-2">
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

    <CRow class="mb-5">
      <CCol>
        {{ docs.proj_name }} / {{ docs.cate_name }} ({{
          timeFormat(docs.created as string, true, '/')
        }})
      </CCol>
      <CCol></CCol>
    </CRow>

    <CRow class="mb-5">
      <CCol>
        <div v-html="sanitizeHtml(docs.content)" />
      </CCol>
    </CRow>

    <!--    <CRow class="mb-5">-->
    <!--      <CCol>-->
    <!--        <CRow>-->
    <!--          <CCol><h5>링크</h5></CCol>-->
    <!--        </CRow>-->

    <!--        <CRow class="mb-2">-->
    <!--          <CCol>-->
    <!--            <PostedLink />-->
    <!--          </CCol>-->
    <!--        </CRow>-->

    <!--        <CRow>-->
    <!--          <CCol>-->
    <!--            <router-link to="#" @click.prevent="1">링크추가</router-link>-->
    <!--          </CCol>-->
    <!--        </CRow>-->
    <!--      </CCol>-->
    <!--    </CRow>-->

    <CRow>
      <CCol>
        <CRow>
          <CCol><h5>파일</h5></CCol>
        </CRow>

        <CRow class="mb-2">
          <CCol>
            <table>
              <tr v-for="file in docs.files" :key="file.pk as number">
                <PostedFile :file="file" @file-delete="fileDelete" />
              </tr>
            </table>
          </CCol>
        </CRow>

        <!--        <CRow>-->
        <!--          <CCol>-->
        <!--            <router-link to="#" @click.prevent="1">파일추가</router-link>-->
        <!--          </CCol>-->
        <!--        </CRow>-->
      </CCol>
    </CRow>

    <CRow class="mt-5">
      <CCol class="text-right">
        <CButton color="light" @click="router.replace({ name: '(문서)' })" size="sm">
          목록으로
        </CButton>
      </CCol>
    </CRow>
  </div>
</template>
