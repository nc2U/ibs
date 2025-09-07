<script lang="ts" setup>
import { type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { btnLight } from '@/utils/cssMixins.ts'
import { timeFormat } from '@/utils/baseMixins'
import type { TrashDocs } from '@/store/types/docs'
import DOMPurify from 'dompurify'

const props = defineProps({
  category: { type: Number, default: undefined },
  docs: { type: Object as PropType<TrashDocs>, default: null },
  viewRoute: { type: String, required: true },
  currPage: { type: Number, required: true },
})

const emit = defineEmits(['restore-docs', 'delete-docs'])

const restoreDocs = () => emit('restore-docs', props.docs?.pk)
const deleteDocs = () => emit('delete-docs', props.docs?.pk)

const router = useRouter()
</script>

<template>
  <div v-if="docs" class="m-0 p-0">
    <CRow class="mt-3">
      <CCol md="8">
        <h5>{{ docs.title }}</h5>
      </CCol>

      <CCol class="pt-1 pr-3 text-right">
        [<span>{{ docs.type_name }}</span>
        <span v-if="docs.cate_name"> &gt; {{ docs.cate_name }} </span>]
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="text-blue-grey mb-5">
      <CCol>
        <small class="mr-3">작성자 : {{ docs.creator }}</small>
      </CCol>

      <CCol class="text-right" md="6">
        <small>
          <v-icon icon="mdi-calendar-clock" size="small" />
          <span class="ml-2">{{ timeFormat(docs?.created ?? '') }}</span>
        </small>
        <small class="ml-3">
          <v-icon icon="mdi-delete-clock" size="small" />
          <span class="ml-2">{{ timeFormat(docs?.deleted ?? '') }}</span>
        </small>
      </CCol>
    </CRow>

    <CRow class="my-5 p-3" id="print-area">
      <CCol>
        <div v-html="DOMPurify.sanitize(docs.content)" />
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="py-2">
      <CCol class="text-right">
        <v-btn-group density="compact" role="group">
          <v-btn :color="btnLight" @click="router.push({ name: `${viewRoute}` })"> 목록으로</v-btn>
          <v-btn color="success" @click="restoreDocs"> 복원하기</v-btn>
          <v-btn color="warning" @click="deleteDocs"> 삭제하기</v-btn>
        </v-btn-group>
      </CCol>
    </CRow>
  </div>
</template>

<style lang="scss" scoped>
.social i {
  cursor: pointer;
}

.social i:hover {
  color: darkslateblue;
}
</style>
