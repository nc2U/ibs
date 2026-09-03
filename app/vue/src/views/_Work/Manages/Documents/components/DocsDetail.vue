<script lang="ts" setup>
import { computed, onMounted, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import type { Docs } from '@/store/types/docs'
import { useRoute, useRouter } from 'vue-router'
import { timeFormat } from '@/utils/baseMixins'
import { storeToRefs } from 'pinia'
import PostInfo from '@/components/OtherParts/PostInfo.vue'
import MDContent from '@/components/OtherParts/MDContent.vue'
import PostedFile from '@/components/OtherParts/PostedFile.vue'
import PostedLink from '@/components/OtherParts/PostedLink.vue'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, required: true },
  heatedPage: { type: Array as PropType<number[]>, default: () => [] },
})

const emit = defineEmits(['docs-hit'])

const [route, router] = [useRoute(), useRouter()]

const { workManager } = storeToRefs(useAccount())

const docId = computed(() => Number(route.params.docId))

// ── 보안 등급별 뱃지 스타일 헬퍼 (절제된 모노/소프트 톤) ─────────────────────
const securityLevelInfo = computed(() => {
  const level = props.docs?.security_level ?? '3'
  switch (level) {
    case '1':
      return {
        color: 'warning',
        icon: 'mdi-lock-outline',
        label: '1등급 비공개',
        tooltip: '1등급: 작성자 및 지정된 허가자만 열람 가능',
      }
    case '2': {
      const dept = props.docs?.creator_dept_name
      return {
        color: 'grey-darken-1',
        icon: 'mdi-account-group-outline',
        label: dept ? `2등급 팀 (${dept})` : '2등급 팀공개',
        tooltip: dept
          ? `2등급: [${dept}] 부서원만 열람 가능`
          : '2등급: 작성자의 소속 부서원 열람 가능',
      }
    }
    case '3':
      return {
        color: 'grey-darken-1',
        icon: 'mdi-folder-account-outline',
        label: '3등급 프로젝트',
        tooltip: '3등급: 워크스페이스 멤버 열람 가능',
      }
    case '4':
      return {
        color: 'grey',
        icon: 'mdi-earth',
        label: '4등급 전사공개',
        tooltip: '4등급: 사원 전체 열람 가능',
      }
    default:
      return {
        color: 'grey',
        icon: 'mdi-shield-outline',
        label: '보안문서',
        tooltip: '보안 문서',
      }
  }
})

onMounted(() => {
  if (docId.value && !props.heatedPage?.includes(docId.value)) {
    emit('docs-hit', docId.value)
  }
})
</script>

<template>
  <div v-if="docs" class="pa-5 rounded border bg-more-light">
    <CRow class="mb-2">
      <CCol class="d-flex align-center gap-2">
        <h4 class="font-weight-bold mb-1">
          {{ docs.title }}
          <v-chip
            v-if="docs.is_pinned"
            label
            size="x-small"
            color="brown-lighten-1"
            class="ml-2 font-weight-bold"
            style="vertical-align: middle"
          >
            <v-icon start icon="mdi-pin" color="danger" size="x-small" class="rotate-45" />
            고정
          </v-chip>

          <!-- 보안 등급 뱃지 (절제된 outlined / tonal 스타일) -->
          <v-tooltip location="top" :text="securityLevelInfo.tooltip">
            <template #activator="{ props: tooltipProps }">
              <v-chip
                v-bind="tooltipProps"
                label
                size="x-small"
                :color="securityLevelInfo.color"
                :variant="docs.security_level === '1' ? 'tonal' : 'outlined'"
                class="ml-2"
                style="vertical-align: middle"
              >
                <v-icon start :icon="securityLevelInfo.icon" size="x-small" />
                {{ securityLevelInfo.label }}
              </v-chip>
            </template>
          </v-tooltip>

          <!-- 관리자 숨김 뱃지 -->
          <v-tooltip v-if="docs.is_blind" location="top" text="관리자에 의해 숨김 처리된 문서">
            <template #activator="{ props: tooltipProps }">
              <v-chip
                v-bind="tooltipProps"
                label
                size="x-small"
                color="error"
                variant="tonal"
                class="ml-2 font-weight-medium"
                style="vertical-align: middle"
              >
                <v-icon start icon="mdi-eye-off" size="x-small" />
                BLIND
              </v-chip>
            </template>
          </v-tooltip>
        </h4>
      </CCol>
    </CRow>

    <CRow class="text-muted text-caption">
      <CCol>
        <span>{{ docs.proj_name }}</span>
        <v-icon icon="mdi-chevron-right" size="small" class="mx-1" />
        <span>{{ docs.cate_name }}</span>
        <v-icon icon="mdi-calendar-range" size="small" class="ml-3 mr-1" />
        <span>{{ timeFormat(docs.created as string, 'short', '/') }}</span>
      </CCol>
    </CRow>

    <v-divider class="my-2" />

    <!-- 관리자 숨김 문서 안내만 띄움 -->
    <v-alert
      v-if="docs.is_blind"
      type="error"
      variant="tonal"
      density="compact"
      class="mb-4"
      icon="mdi-eye-off"
    >
      <span>이 문서는 관리자에 의해 <strong>숨김(BLIND)</strong> 처리된 문서입니다.</span>
    </v-alert>

    <PostInfo :docs="docs" />

    <CRow class="mb-5">
      <CCol class="d-flex align-center flex-wrap gap-4 text-body-2">
        <span>
          <small class="text-muted">카테고리: </small>
          <strong>{{ docs.cate_name }}</strong>
        </span>
        <span v-if="docs.execution_date">
          <small class="text-muted">시행일자: </small>
          <strong>{{ docs.execution_date }}</strong>
        </span>
        <span>
          <small class="text-muted">보안등급: </small>
          <strong :class="docs.security_level === '1' ? 'text-warning' : 'text-body-2'">
            {{ docs.security_level_desc ?? securityLevelInfo.label }}
          </strong>
        </span>
      </CCol>
    </CRow>

    <div v-if="docs.description" class="description-section mb-5">
      <h6 class="mb-2 text-muted">문서 요약</h6>
      <div class="p-3 rounded border card-white">
        <MDContent :content="docs.description" />
      </div>
    </div>

    <div class="files-section">
      <CRow class="mb-3 pt-4">
        <CCol>
          <h6 class="mb-2">첨부 파일</h6>
          <p
            v-if="!workManager && (docs.security_level === '1' || docs.is_blind)"
            class="text-muted small"
          >
            <v-icon icon="mdi-lock" size="x-small" class="mr-1" />
            {{ docs.is_blind ? '숨김' : '비공개' }}
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
          <p
            v-if="!workManager && (docs.security_level === '1' || docs.is_blind)"
            class="text-muted small"
          >
            <v-icon icon="mdi-lock" size="x-small" class="mr-1" />
            {{ docs.is_blind ? '숨김' : '비공개' }} 문서의 관련 링크는 열람이 제한됩니다.
          </p>
          <template v-else-if="docs.links && docs.links.length">
            <PostedLink :docs="docs.pk as number" btn-direction="right" :links="docs.links" />
          </template>
          <p v-else class="text-muted small">관련 링크가 없습니다.</p>
        </CCol>
      </CRow>
    </div>

    <v-divider />

    <CRow class="mt-1 pr-0">
      <CCol class="text-right pr-0">
        <v-btn color="light" variant="flat" @click="router.push({ name: '(문서)' })" size="small">
          목록으로
        </v-btn>
      </CCol>
    </CRow>
  </div>
</template>

<style scoped>
.rotate-45 {
  transform: rotate(45deg);
}
</style>
