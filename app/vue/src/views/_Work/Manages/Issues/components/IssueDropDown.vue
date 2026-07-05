<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useRouter } from 'vue-router'
import type { Issue, SimpleIssue } from '@/store/types/work_issue.ts'

const props = defineProps({
  issue: { type: Object as PropType<Issue | SimpleIssue>, required: true },
})

const emit = defineEmits(['watch-control'])

const router = useRouter()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const issueStore = useIssue()
const statusList = computed(() => issueStore.statusList)

const isWatcher = ref(false)

const isCumputedWatcher = computed(() =>
  props.issue?.watchers.map(w => w.pk).includes(userInfo?.value?.pk as number),
)

const watchControl = () => {
  emit('watch-control', props.issue?.pk)
  isWatcher.value = !isWatcher.value
}

const changeStatus = (statusPk: number) => {
  const currentStatusPk =
    typeof props.issue.status === 'object' ? props.issue.status.pk : props.issue.status
  if (currentStatusPk !== statusPk) {
    issueStore.patchIssue(props.issue.pk, { status: statusPk })
  }
}

onBeforeMount(() => (isWatcher.value = isCumputedWatcher.value as any))
</script>

<template>
  <span>
    <v-btn icon variant="text" size="x-small" color="grey-darken-1">
      <v-icon icon="mdi-dots-horizontal" />
      <v-tooltip activator="parent" location="top">Actions</v-tooltip>
      <v-menu activator="parent" location="bottom end" transition="scale-transition">
        <v-list density="compact" class="py-1">
          <v-list-item
            min-height="30px"
            class="py-0"
            @click="
              router.push({
                name: '(업무) - 보기',
                params: { projId: issue.project.slug, issueId: issue.pk },
                query: { edit: '1' },
              })
            "
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-pencil" color="amber" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">편집</v-list-item-title>
          </v-list-item>

          <v-menu open-on-hover location="end" offset="5">
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-list-status" color="primary" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">상태</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item
                v-for="status in statusList"
                :key="status.pk"
                :active="
                  (typeof issue.status === 'object' ? issue.status.pk : issue.status) === status.pk
                "
                min-height="28px"
                class="py-0"
                @click="changeStatus(status.pk)"
              >
                <v-list-item-title class="text-caption">{{ status.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">유형</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">우선순위</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">담당자</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">진척도</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">업무 관람자</v-list-item-title>
          </v-list-item>

          <v-list-item @click="watchControl" min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon
                icon="mdi-star"
                :color="isWatcher ? 'amber' : 'secondary'"
                size="small"
                class="mr-n2"
              />
            </template>
            <v-list-item-title class="text-caption">
              {{ isWatcher ? '관심끄기' : '지켜보기' }}
            </v-list-item-title>
          </v-list-item>

          <v-list-item
            min-height="28px"
            class="py-0"
            @click="
              router.push({
                name: '(업무) - 추가',
                params: { projId: issue.project.slug },
                query: { parent: issue.pk, tracker: issue.tracker.pk },
              })
            "
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-plus-circle" color="success" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">하위 업무 추가</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon icon="mdi-link-edit" color="secondary" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">링크복사</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon icon="mdi-content-copy" color="secondary" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">복사</v-list-item-title>
          </v-list-item>

          <v-list-item disabled min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon icon="mdi-trash-can-outline" color="secondary" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">업무 삭제</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-btn>
  </span>
</template>
