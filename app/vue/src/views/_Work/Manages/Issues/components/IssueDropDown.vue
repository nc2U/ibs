<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { Issue, SimpleIssue } from '@/store/types/work_issue.ts'

const props = defineProps({
  issue: { type: Object as PropType<Issue | SimpleIssue>, required: true },
})

const emit = defineEmits(['watch-control'])

const router = useRouter()

const { can, PERM } = usePerms()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const isWatcher = ref(false)

const isCumputedWatcher = computed(() =>
  props.issue?.watchers.map(w => w.pk).includes(userInfo?.value?.pk as number),
)

const watchControl = () => {
  emit('watch-control', props.issue?.pk)
  isWatcher.value = !isWatcher.value
}

onBeforeMount(() => (isWatcher.value = isCumputedWatcher.value as any))
</script>

<template>
  <span>
    <CDropdown color="secondary" variant="input-group" placement="bottom-end">
      <CDropdownToggle :caret="false" color="light" variant="ghost" size="sm" shape="rounded-pill">
        <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
        <v-tooltip activator="parent" location="top">Actions</v-tooltip>
      </CDropdownToggle>
      <CDropdownMenu>
        <CDropdownItem
          class="form-text"
          @click="
            router.push({
              name: '(업무) - 보기',
              params: { projId: issue.project.slug, issueId: issue.pk },
              query: { edit: '1' },
            })
          "
        >
          <v-icon icon="mdi-pencil" color="amber" size="sm" />
          <span class="text-primary ml-1">편집</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <span class="ml-1">상태</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <span class="ml-1">유형</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <span class="ml-1">우선순위</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <span class="ml-1">담당자</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <span class="ml-1">진척도</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <span class="ml-1">업무 관람자</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" @click="watchControl">
          <v-icon icon="mdi-star" :color="isWatcher ? 'amber' : 'secondary'" size="sm" />
          <span class="text-primary ml-1">{{ isWatcher ? '관심끄기' : '지켜보기' }}</span>
        </CDropdownItem>
        <CDropdownItem
          class="form-text"
          @click="
            router.push({
              name: '(업무) - 추가',
              params: { projId: issue.project.slug },
              query: { parent: issue.pk, tracker: issue.tracker.pk },
            })
          "
        >
          <v-icon icon="mdi-plus-circle" color="success" size="sm" />
          <span class="text-primary ml-1">하위 업무 추가</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon icon="mdi-link-edit" color="secondary" size="sm" />
          <span class="ml-1">링크복사</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon icon="mdi-content-copy" color="secondary" size="sm" />
          <span class="ml-1">복사</span>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon icon="mdi-trash-can-outline" color="secondary" size="sm" />
          <span class="ml-1">업무 삭제</span>
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  </span>
</template>
