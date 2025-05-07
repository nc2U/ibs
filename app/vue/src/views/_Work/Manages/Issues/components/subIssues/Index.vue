<script lang="ts" setup>
import { ref, type PropType, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { cutString } from '@/utils/baseMixins'
import type { SubIssue } from '@/store/types/work'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ subIssues: { type: Array as PropType<SubIssue[]>, default: () => [] } })

const emit = defineEmits(['unlink-sub-issue'])

const router = useRouter()

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
</script>

<template>
  <CRow
    v-for="sub in subIssues"
    :key="sub.pk"
    :class="{ 'bg-info-lighten': selected === sub.pk }"
    class="sub-issue cursor-menu"
    @click="selected = sub.pk"
  >
    <CCol md="6" lg="4" class="pt-1">
      <router-link
        :to="{ name: '(업무) - 보기', params: { issueId: sub.pk } }"
        :class="{ closed: sub.closed }"
      >
        기능 #{{ sub.pk }}
      </router-link>
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
      <span class="mr-3" @click="parentUnlink(sub.pk)">
        <v-icon icon="mdi-link-variant-off" size="sm" color="grey" class="pointer" />
        <v-tooltip activator="parent" location="top"> 관계 지우기 </v-tooltip>
      </span>
      <span>
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
                  name: '(업무) - 보기',
                  params: { issueId: sub.pk },
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
              <v-icon icon="mdi-timer-edit-outline" color="grey" size="sm" />
              작업시간 기록
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
    <template #header>하위 업무 관계 지우기</template>
    <template #default> 계속 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="unlinkSubIssue">확인</v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
.closed {
  color: #999;
  text-decoration: line-through;
}
</style>
