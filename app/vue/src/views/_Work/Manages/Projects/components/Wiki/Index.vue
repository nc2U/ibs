<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import MdEditor from '@/components/MdEditor/Index.vue'

const emit = defineEmits(['aside-visible'])

const route = useRoute()

const form = ref({
  wiki: '',
  description: '',
  files: [],
})

const capitalize = (str: string) => `${str.charAt(0).toUpperCase()}${str.slice(1)}`

const wikiTitle = computed(() =>
  route.params.title ? capitalize(route.params.title as string) : 'Wiki',
)

onBeforeMount(() => {
  emit('aside-visible', false)
  form.value.wiki = `# ${wikiTitle.value}`
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ wikiTitle }}</h5>
    </CCol>
  </CRow>

  <CRow class="mb-3">
    <CCol sm="11">
      <MdEditor v-model="form.wiki" />
    </CCol>
  </CRow>

  <CRow class="mb-3">
    <CFormLabel for="desc" class="col-form-label text-center col-1">설명</CFormLabel>
    <CCol class="col-10">
      <CFormInput v-model="form.description" id="desc" />
    </CCol>
  </CRow>

  <CRow class="mb-4">
    <CFormLabel for="files" class="col-form-label text-center col-1">파일</CFormLabel>
    <CCol class="col-10">
      <CFormInput v-model="form.files" type="file" id="files" />
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <v-btn color="primary">저장</v-btn>
      <v-btn color="light">취소</v-btn>
    </CCol>
  </CRow>
</template>
