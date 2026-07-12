<script lang="ts" setup>
import { ref, type PropType, watchEffect } from 'vue'
import { cutString } from '@/utils/baseMixins'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { SubIssue } from '@/store/types/work_issue.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ sub: { type: Object as PropType<SubIssue>, required: true } })

const emit = defineEmits(['unlink-sub-issue'])

const route = useRoute()
const router = useRouter()
const { can, PERM } = usePerms()

const selected = ref<number | null>(null)

const handleClickOutside = (event: any) => {
  if (!event.target.closest('.sub-issue')) selected.value = null
}

watchEffect(() => {
  if (selected.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

const delSubRef = ref()
const child = ref<number | null>(null)

const parentUnlink = (pk: number) => {
  child.value = pk
  delSubRef.value.callModal()
}

const unlinkSubIssue = () => {
  emit('unlink-sub-issue', child.value)
  child.value = null
  delSubRef.value.close()
}

const projId = route.params.projId as string
const detailRouteName = projId ? '(업무) - 보기' : '업무 - 보기'
const detailRouteParams = (id: number) => (projId ? { projId, issueId: id } : { issueId: id })
</script>

<template>
  <CRow
    class="sub-issue cursor-menu"
    :class="{ 'bg-info-lighten': selected === sub.pk }"
    @click="selected = sub.pk"
  >
    <CCol md="6" lg="4" class="pt-1">
      <router-link
        v-if="can(PERM.ISSUE_READ)"
        :to="{ name: detailRouteName, params: detailRouteParams(sub.pk) }"
        :class="{ closed: sub.closed }"
      >
        기능 #{{ sub.pk }}
      </router-link>
      <span v-else :class="{ closed: sub.closed }">기능 #{{ sub.pk }}</span>
      : {{ sub.subject }}
    </CCol>
    <CCol class="col-sm-6 col-md-3 col-lg-4 text-right pt-1">
      <span class="mr-3">{{ sub.status }}</span>
      <span v-if="sub.assigned_to" class="mr-3">
        <router-link :to="{ name: '사용자 - 보기', params: { userId: sub.assigned_to.pk } }">
          {{ cutString(sub.assigned_to.username, 9) }}
        </router-link>
      </span>
      <span class="mr-3">{{ sub?.start_date }}</span>
    </CCol>
    <CCol class="col-sm-6 col-md-3 col-lg-4 text-right">
      <span class="mr-3">
        <CProgress
          color="green-lighten-3"
          :value="sub?.done_ratio ?? 0"
          style="width: 100px; float: left; margin-top: 7px"
          height="14"
        />
      </span>
      <v-btn
        v-if="can(PERM.ISSUE_SUB_MANAGE)"
        variant="plain"
        class="mr-3"
        @click="parentUnlink(sub.pk)"
      >
        <v-icon icon="mdi-link-variant-off" size="16" />
        <v-tooltip activator="parent" location="start"> 관계 지우기 </v-tooltip>
      </v-btn>
      <span v-if="can(PERM.ISSUE_SUB_MANAGE)">
        <CDropdown color="secondary" variant="input-group" placement="bottom-end">
          <CDropdownToggle
            :caret="false"
            color="light"
            variant="ghost"
            size="sm"
            shape="rounded-pill"
          >
            <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
            <v-tooltip activator="parent" location="top">Actions</v-tooltip>
          </CDropdownToggle>
          <CDropdownMenu>
            <CDropdownItem
              class="form-text"
              @click="
                router.push({
                  name: detailRouteName,
                  params: detailRouteParams(sub.pk),
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
              <!--                    <router-link to="">-->
              <v-icon color="amber" size="sm" />
              유형
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <v-icon color="amber" size="sm" />
              <!--                    <router-link to=""> -->
              우선순위
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <v-icon color="amber" size="sm" />
              <!--                    <router-link to=""> -->
              담당자
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <v-icon color="amber" size="sm" />
              <!--                    <router-link to=""> -->
              진척도
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <!--                    <router-link to="">-->
              <v-icon icon="mdi-star" color="secondary" size="sm" />
              지켜보기
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <!--                    <router-link to="">-->
              <v-icon icon="mdi-link-plus" color="grey" size="sm" />
              링크 복사
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <!--                    <router-link to="">-->
              <v-icon icon="mdi-content-copy" color="grey" size="sm" />
              복사
              <!--                    </router-link>-->
            </CDropdownItem>
            <CDropdownItem class="form-text" disabled>
              <!--                    <router-link to="">-->
              <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" />
              업무 삭제
              <!--                    </router-link>-->
            </CDropdownItem>
          </CDropdownMenu>
        </CDropdown>
      </span>
    </CCol>
  </CRow>

  <ConfirmModal ref="delSubRef">
    <template #header>하위 업무 관계 삭제</template>
    <template #default>상위 업무와의 관계를 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" size="small" @click="unlinkSubIssue">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
