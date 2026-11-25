<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { timeFormat } from '@/utils/baseMixins'
import type { TrashDocs } from '@/store/types/docs'
import DOMPurify from 'dompurify'

const props = defineProps({
  docs: { type: Object as PropType<TrashDocs | null>, default: null },
  viewRoute: { type: String, required: true },
})

const emit = defineEmits(['restore-docs', 'delete-docs'])

const router = useRouter()
const accStore = useAccount()

const canManage = computed(
  () =>
    !!props.docs &&
    (!!accStore.superAuth ||
      !!accStore.workManager ||
      (!!props.docs.creator && props.docs.creator === accStore.userInfo?.username)),
)
</script>

<template>
  <div v-if="docs" class="m-0 p-0">
    <CRow class="mt-3 align-items-center">
      <CCol md="8">
        <h5 class="mb-0">{{ docs.title }}</h5>
      </CCol>

      <CCol class="pt-1 pe-3 text-end text-medium-emphasis">
        [
        <span v-if="docs.project_name">{{ docs.project_name }} · </span>
        <span>{{ docs.type_name }}</span>
        <span v-if="docs.cate_name"> &gt; {{ docs.cate_name }}</span>
        ]
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="text-medium-emphasis mb-4">
      <CCol>
        <small class="me-3">작성자 : {{ docs.creator || '-' }}</small>
      </CCol>

      <CCol class="text-end" md="6">
        <small>
          <v-icon icon="mdi-calendar-clock" size="small" />
          <span class="ms-1">{{ timeFormat(docs.created ?? '') }}</span>
        </small>
        <small class="ms-3">
          <v-icon icon="mdi-delete-clock" size="small" />
          <span class="ms-1">{{ timeFormat(docs.deleted ?? '') }}</span>
        </small>
      </CCol>
    </CRow>

    <CRow class="my-4 p-3 border rounded">
      <CCol>
        <div v-html="DOMPurify.sanitize(docs.description || '')" />
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="py-2">
      <CCol class="text-end">
        <v-btn-group density="compact" role="group">
          <v-btn color="light" @click="router.push({ name: viewRoute })">목록으로</v-btn>
          <v-btn v-if="canManage" color="success" @click="emit('restore-docs', docs.pk)">
            복원하기
          </v-btn>
          <v-btn v-if="canManage" color="error" @click="emit('delete-docs', docs.pk)">
            완전 삭제
          </v-btn>
        </v-btn-group>
      </CCol>
    </CRow>
  </div>
</template>
