<script lang="ts" setup>
import { ref, computed, type ComputedRef, inject, type PropType, onBeforeMount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Issue, SimpleIssue } from '@/store/types/work_issue.ts'
import type { User } from '@/store/types/accounts'

const props = defineProps({
  issue: { type: Object as PropType<Issue | SimpleIssue>, required: true },
})

const emit = defineEmits(['watch-control'])

const [route, router] = [useRoute(), useRouter()]

const userInfo = inject<ComputedRef<User>>('userInfo')

const isWatcher = ref(false)

const isCumputedWatcher = computed(() =>
  props.issue?.watchers.map(w => w.pk).includes(userInfo?.value?.pk as number),
)

const watchControl = () => {
  const payload = isWatcher.value
    ? { del_watcher: userInfo?.value?.pk }
    : { watchers: [userInfo?.value?.pk] }
  emit('watch-control', payload, props.issue?.pk)
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
          <router-link to="">
            <v-icon icon="mdi-pencil" color="amber" size="sm" />
            편집
          </router-link>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <!--                      <router-link to="">-->
          상태
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <!--                      <router-link to="">-->
          유형
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <!--                      <router-link to=""> -->
          우선순위
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <!--                      <router-link to=""> -->
          담당자
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <!--                      <router-link to=""> -->
          진척도
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <v-icon size="sm" />
          <!--                      <router-link to=""> -->
          업무 관람자
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" @click="watchControl">
          <router-link to="">
            <v-icon icon="mdi-star" :color="isWatcher ? 'amber' : 'secondary'" size="sm" />
            {{ isWatcher ? '관심끄기' : '지켜보기' }}
          </router-link>
        </CDropdownItem>
        <CDropdownItem
          class="form-text"
          @click="
            router.push({
              name: route.params.projId ? '(소요시간) - 추가' : '소요시간 - 추가',
              query: { issue_id: issue.pk },
            })
          "
        >
          <router-link to="">
            <v-icon icon="mdi-calendar-clock" color="secondary" size="sm" />
            작업시간 기록
          </router-link>
        </CDropdownItem>
        <CDropdownItem
          class="form-text"
          @click="
            router.push({
              name: '(업무) - 추가',
              query: { parent: issue.pk, tracker: issue.tracker.pk },
            })
          "
        >
          <router-link to="">
            <v-icon icon="mdi-plus-circle" color="success" size="sm" />
            하위 업무 추가
          </router-link>
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <!--                      <router-link to="">-->
          <v-icon icon="mdi-link-edit" color="secondary" size="sm" />
          링크복사
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <!--                      <router-link to="">-->
          <v-icon icon="mdi-content-copy" color="secondary" size="sm" />
          복사
          <!--                      </router-link>-->
        </CDropdownItem>
        <CDropdownItem class="form-text" disabled>
          <!--                      <router-link to="">-->
          <v-icon icon="mdi-trash-can-outline" color="secondary" size="sm" />
          업무 삭제
          <!--                      </router-link>-->
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  </span>
</template>
