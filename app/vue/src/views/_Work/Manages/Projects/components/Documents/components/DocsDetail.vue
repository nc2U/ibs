<script lang="ts" setup>
import { computed, onMounted, type PropType, ref } from 'vue'
import { useDocs } from '@/store/pinia/docs'
import type { Docs } from '@/store/types/docs'
import { useRoute, useRouter } from 'vue-router'
import { timeFormat } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { storeToRefs } from 'pinia'
import { useAccount } from '@/store/pinia/account.ts'
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

const { can, PERM } = usePerms()
const canDocsUpdate = computed(() => can(PERM.DOCS_UPDATE))
const canDocsDelete = computed(() => can(PERM.DOCS_DELETE))

const { workManager } = storeToRefs(useAccount())

const docId = computed(() => Number(route.params.docId))

const modalAction = () => {
  docStore.deleteDocs(props.docs.pk as number, {})
  refConfirmModal.value.close()
  router.push({ name: '(문서)' })
}

onMounted(() => {
  if (docId.value && !props.heatedPage?.includes(docId.value)) {
    emit('docs-hit', docId.value)
  }
})
</script>

<template>
  <div v-if="docs" class="pa-4">
    <CRow class="mb-2">
      <CCol class="d-flex align-center gap-2">
        <h4 class="font-weight-bold mb-1">
          {{ docs.title }}
          <v-tooltip
            v-if="docs.is_secret || docs.is_blind"
            location="right"
            :text="docs.is_secret ? '비밀 문서' : '숨김 문서'"
          >
            <template #activator="{ props: tooltipProps }">
              <v-chip
                v-bind="tooltipProps"
                label
                size="small"
                :color="docs.is_secret ? 'warning' : 'error'"
                variant="tonal"
                class="ml-2"
                style="vertical-align: middle"
              >
                <v-icon start :icon="docs.is_secret ? 'mdi-lock' : 'mdi-eye-off'" size="small" />
                {{ docs.is_secret ? 'SECRET' : 'BLIND' }}
              </v-chip>
            </template>
          </v-tooltip>
        </h4>
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

    <v-alert
      v-if="docs.is_secret || docs.is_blind"
      :type="docs.is_secret ? 'warning' : 'error'"
      variant="tonal"
      density="compact"
      class="mb-4"
      :icon="docs.is_secret ? 'mdi-lock' : 'mdi-eye-off'"
    >
      <span>
        이 문서는 <strong>{{ docs.is_secret ? '비밀' : '숨김' }} 문서</strong> 입니다.
        <span v-if="!workManager">열람 권한이 없어 일부 내용이 제한됩니다.</span>
      </span>
    </v-alert>

    <PostInfo :docs="docs" class="mb-4" />

    <CRow class="mb-5">
      <CCol>
        <span class="mr-3">
          <small class="text-muted">카테고리: </small>
          <strong>{{ docs.cate_name }}</strong>
        </span>
        <span v-if="docs.execution_date">
          <small class="text-muted">시행일자: </small>
          <strong>{{ docs.execution_date }}</strong>
        </span>
      </CCol>
    </CRow>

    <div v-if="docs.description" class="description-section mb-5">
      <h6 class="mb-2 text-muted">문서 요약</h6>
      <div class="p-3 bg-more-light rounded border">
        <PostContent :description="docs.description" />
      </div>
    </div>

    <div class="files-section">
      <CRow class="mb-3 pt-4">
        <CCol>
          <h6 class="mb-2">첨부 파일</h6>
          <p v-if="!workManager && (docs.is_secret || docs.is_blind)" class="text-muted small">
            <v-icon icon="mdi-lock" size="x-small" class="mr-1" />
            {{ docs.is_secret ? '비밀' : '숨김' }}
            문서의 첨부 파일은 열람이 제한됩니다.
          </p>
          <template v-else-if="docs.files && docs.files.length">
            <PostedFile :docs="docs.pk as number" btn-direction="right" :files="docs.files" />
          </template>

          <p v-else class="text-muted small">첨부 파일이 없습니다.</p>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol>
          <h6 class="mb-2">관련 링크</h6>
          <p v-if="!workManager && (docs.is_secret || docs.is_blind)" class="text-muted small">
            <v-icon icon="mdi-lock" size="x-small" class="mr-1" />
            {{ docs.is_secret ? '비밀' : '숨김' }} 문서의 관련 링크는 열람이 제한됩니다.
          </p>
          <template v-else-if="docs.links && docs.links.length">
            <PostedLink :docs="docs.pk as number" btn-direction="right" :links="docs.links" />
          </template>
          <p v-else class="text-muted small">관련 링크가 없습니다.</p>
        </CCol>
      </CRow>
    </div>

    <v-divider class="mb-3" />

    <CRow class="mt-4">
      <CCol class="text-right">
        <v-btn color="light" variant="flat" @click="router.back()" size="small" class="mr-2">
          목록으로
        </v-btn>

        <v-btn
          v-if="canDocsUpdate"
          color="success"
          size="small"
          class="mr-2"
          :to="{ name: '(문서) - 편집' }"
        >
          <v-icon icon="mdi-pencil" size="small" class="mr-1" />
          편집
        </v-btn>

        <v-btn
          v-if="canDocsDelete"
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
