<script lang="ts" setup>
import { computed, onMounted, ref, watch, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import { usePerms } from '@/composables/usePerms'
import { bgLight } from '@/utils/cssMixins'
import type { User } from '@/store/types/accounts'
import type { IssueProject, Member, Role } from '@/store/types/work_project'

const props = defineProps({
  user: { type: Object as PropType<User | null>, default: null },
})

const { can, PERM } = usePerms()
const accStore = useAccount()
const comStore = useCompany()
const workStore = useWork()

const roleList = computed<Role[]>(() => workStore.roleList)
const superAuth = computed(() => Boolean(accStore.superAuth))

// 프로젝트 비즈니스 데이터 관리(ibs_pr_manage) 역할 목록 필터링 (비슈퍼유저는 보안 격리 역할 제외)
const ibsRoles = computed(() =>
  roleList.value.filter(
    r => r.category === 'ibs_pr_manage' && (superAuth.value || !r.is_confidential),
  ),
)

// 선택 회사 기준 사용 가능한 부동산 개발 (type='2', status='1') 프로젝트 목록
const allDevProjects = computed(() => {
  const comPk = comStore.company?.pk
  const comName = comStore.company?.name
  return workStore.allReadableProjects.filter(p => {
    if (p.type !== '2' || p.status !== '1') return false
    if (!comPk) return true
    return p.company === comPk || (Boolean(comName) && String(p.company ?? '') === comName)
  })
})

const canManageProject = (proj: IssueProject) =>
  Boolean(proj.slug ? can(PERM.PROJECT_MEMBER, proj.slug) : proj.pk && can(PERM.PROJECT_MEMBER, proj.pk))

const isRoleAllowed = (proj: IssueProject, rolePk: number) => {
  if (superAuth.value) return true
  if (!proj.allowed_roles || proj.allowed_roles.length === 0) return true
  return proj.allowed_roles.some(ar => Number(ar.pk) === Number(rolePk))
}

const memberList = ref<Member[]>([])
const loading = ref(false)
const mutatingProjects = ref<Record<number, boolean>>({})
let fetchMemberSeq = 0

// 선택된 사용자가 각 프로젝트에서 가지는 Member 정보 로드
const fetchUserMembers = async (showSpinner = true) => {
  const targetUserPk = props.user?.pk
  const seq = ++fetchMemberSeq
  if (!targetUserPk) {
    memberList.value = []
    loading.value = false
    return
  }
  if (showSpinner) loading.value = true
  try {
    const response = await workStore.fetchMemberList(targetUserPk)
    if (seq !== fetchMemberSeq) return
    memberList.value = Array.isArray(response) ? (response as Member[]) : []
  } catch (error) {
    if (seq === fetchMemberSeq) memberList.value = []
    console.error('Failed to fetch user members:', error)
  } finally {
    if (seq === fetchMemberSeq && showSpinner) {
      loading.value = false
    }
  }
}

watch(
  () => props.user?.pk,
  () => fetchUserMembers(true),
  { immediate: true },
)

watch(
  () => comStore.company?.pk,
  comPk => {
    workStore.fetchAllProjectList('', comPk ?? '')
  },
)

// 특정 프로젝트에서 해당 역할을 부여받았는지 확인
const hasRole = (projPk: number, rolePk: number) => {
  const member = memberList.value.find(m => m.project.pk === projPk)
  if (!member) return false
  return member.roles.some(r => r.pk === rolePk)
}

// 멤버의 역할 토글 및 업데이트
const toggleRole = async (proj: IssueProject, rolePk: number) => {
  const projPk = proj.pk
  if (!projPk || !props.user?.pk) return
  if (!canManageProject(proj) || !isRoleAllowed(proj, rolePk)) return
  if (mutatingProjects.value[projPk]) return

  const member = memberList.value.find(m => m.project.pk === projPk)
  mutatingProjects.value = { ...mutatingProjects.value, [projPk]: true }

  try {
    let ok = false
    if (!member) {
      if (!proj.slug) return
      const created = await workStore.createMember({
        user: props.user.pk,
        roles: [rolePk],
        slug: proj.slug,
      })
      ok = Boolean(created)
    } else {
      const currentRolePks = member.roles.map(r => r.pk)
      const index = currentRolePks.indexOf(rolePk)
      if (index === -1) currentRolePks.push(rolePk)
      else currentRolePks.splice(index, 1)

      if (currentRolePks.length === 0) {
        ok = await workStore.deleteMember(member.pk, props.user.pk)
      } else {
        const updated = await workStore.patchMember({
          pk: member.pk,
          roles: currentRolePks,
        })
        ok = Boolean(updated)
      }
    }

    if (ok) {
      await fetchUserMembers(false)
      if (props.user.pk === accStore.userInfo?.pk) {
        await workStore.fetchMyProjectsList()
      }
    }
  } finally {
    const nextState = { ...mutatingProjects.value }
    delete nextState[projPk]
    mutatingProjects.value = nextState
  }
}

onMounted(() => {
  workStore.fetchAllProjectList('', comStore.company?.pk ?? '')
  workStore.fetchRoleList()
})
</script>

<template>
  <div class="mt-4">
    <!-- 프로젝트별 비즈니스 데이터 권한(Role) 매핑 -->
    <CRow>
      <CCol>
        <h6 class="fw-bold mb-3 d-flex align-items-center justify-content-between">
          <span>
            <v-icon icon="mdi-shield-key-outline" color="primary" size="small" class="me-2" />
            프로젝트 별 담당 권한
          </span>
          <small v-if="comStore.company?.name" class="text-body-secondary fw-normal">
            기준 회사: {{ comStore.company.name }}
          </small>
        </h6>

        <div v-if="!user" class="text-center py-4 text-muted border rounded" :class="bgLight">
          사용자를 선택해 주세요.
        </div>

        <div v-else-if="loading" class="text-center py-4">
          <v-progress-circular indeterminate color="primary" />
        </div>

        <div
          v-else-if="allDevProjects.length === 0"
          class="text-center py-4 text-muted border rounded"
          :class="bgLight"
        >
          선택된 회사에 사용 가능한 부동산 개발 프로젝트가 존재하지 않습니다.
        </div>

        <div v-else class="space-y-4">
          <CCard v-for="proj in allDevProjects" :key="proj.pk" class="mb-3">
            <CCardHeader class="bg-more-light d-flex align-items-center justify-content-between">
              <span class="fw-bold text-body d-flex align-items-center">
                <v-icon icon="mdi-folder" color="grey" size="small" class="pt-1 me-1" />
                {{ proj.name }}
                <v-chip
                  v-if="!proj.is_public"
                  color="danger"
                  size="x-small"
                  variant="flat"
                  class="ms-2 p-2 fw-bold text-white"
                  density="comfortable"
                >
                  <v-icon icon="mdi-lock" size="x-small" class="me-2" />
                  비공개
                </v-chip>
                <v-chip
                  v-if="!canManageProject(proj)"
                  color="warning"
                  size="x-small"
                  variant="tonal"
                  class="ms-2"
                >
                  할당 권한 없음
                </v-chip>
                <v-progress-circular
                  v-if="proj.pk && mutatingProjects[proj.pk]"
                  indeterminate
                  size="14"
                  width="2"
                  color="primary"
                  class="ms-2"
                />
              </span>
              <v-chip size="x-small" variant="tonal" color="grey">Business Perms</v-chip>
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol v-if="ibsRoles.length === 0" class="text-muted small">
                  시스템에 등록된 프로젝트 관리 관련 역할([ibs_pr_manage] 카테고리)이 없습니다.
                </CCol>
                <template v-else>
                  <CCol v-for="role in ibsRoles" :key="role.pk" xs="12" sm="6" md="4" class="py-1">
                    <CFormCheck
                      :id="`member-role-${proj.pk}-${role.pk}`"
                      :label="
                        isRoleAllowed(proj, role.pk) ? role.name : `${role.name} (미허용)`
                      "
                      :checked="hasRole(proj.pk || 0, role.pk)"
                      :disabled="
                        !canManageProject(proj) ||
                        !isRoleAllowed(proj, role.pk) ||
                        Boolean(proj.pk && mutatingProjects[proj.pk])
                      "
                      @change="toggleRole(proj, role.pk)"
                    />
                  </CCol>
                </template>
              </CRow>
            </CCardBody>
          </CCard>
        </div>
      </CCol>
    </CRow>
  </div>
</template>

<style scoped>
.space-y-4 > * + * {
  margin-top: 1rem;
}
</style>
