<script lang="ts" setup>
import { ref, computed, onMounted, watch, type PropType } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import type { User } from '@/store/types/accounts'
import type { Role, Member } from '@/store/types/work_project'
import { write_auth_manage } from '@/utils/pageAuth'

const props = defineProps({
  user: { type: Object as PropType<User | null>, default: null },
})

const workStore = useWork()
const roleList = computed<Role[]>(() => workStore.roleList)

// ibs_global 카테고리의 역할 목록 필터링
const ibsRoles = computed(() => roleList.value.filter(r => r.category === 'ibs_global'))

// 사용 가능한 전체 부동산 개발 (type='2', status='1') 프로젝트 목록
const allDevProjects = computed(() =>
  workStore.allReadableProjects.filter(p => p.type === '2' && p.status === '1'),
)

const memberList = ref<Member[]>([])
const loading = ref(false)

// 선택된 사용자가 각 프로젝트에서 가지는 Member 정보 로드
const fetchUserMembers = async () => {
  if (!props.user?.pk) {
    memberList.value = []
    return
  }
  loading.value = true
  try {
    const response = await workStore.fetchMemberList(props.user.pk)
    if (response) {
      memberList.value = response as Member[]
    }
  } catch (error) {
    console.error('Failed to fetch user members:', error)
  } finally {
    loading.value = false
  }
}

watch(
  () => props.user,
  () => fetchUserMembers(),
  { immediate: true },
)

// 특정 프로젝트에서 해당 역할을 부여받았는지 확인
const hasRole = (projPk: number, rolePk: number) => {
  const member = memberList.value.find(m => m.project.pk === projPk)
  if (!member) return false
  return member.roles.some(r => r.pk === rolePk)
}

// 멤버의 역할 토글 및 업데이트
const toggleRole = async (projPk: number, rolePk: number) => {
  if (!write_auth_manage.value || !props.user?.pk) return

  const member = memberList.value.find(m => m.project.pk === projPk)

  if (!member) {
    // 1. 해당 프로젝트에 멤버로 등록되어 있지 않은 경우 -> 멤버 생성 및 역할 할당
    const proj = workStore.allReadableProjects.find(p => p.pk === projPk)
    if (!proj?.slug) return

    try {
      loading.value = true
      await workStore.createMember({
        project: projPk,
        slug: proj.slug,
        user_id: props.user.pk,
        role_ids: [rolePk],
      } as any)
      await fetchUserMembers()
    } catch (error) {
      console.error('Failed to create member and assign role:', error)
    } finally {
      loading.value = false
    }
  } else {
    // 2. 이미 멤버인 경우 -> 역할 추가 또는 제거
    const currentRolePks = member.roles.map(r => r.pk)
    const index = currentRolePks.indexOf(rolePk)

    if (index === -1) {
      currentRolePks.push(rolePk)
    } else {
      currentRolePks.splice(index, 1)
    }

    try {
      loading.value = true
      if (currentRolePks.length === 0) {
        // 지정된 역할이 0개가 되면 멤버십 완전히 삭제(탈퇴)
        await workStore.deleteMember(member.pk)
      } else {
        // 역할 목록 수정
        await workStore.patchMember({
          pk: member.pk,
          roles: currentRolePks,
        })
      }
      await fetchUserMembers()
    } catch (error) {
      console.error('Failed to update member roles:', error)
    } finally {
      loading.value = false
    }
  }
}

onMounted(() => {
  workStore.fetchAllProjectList()
  workStore.fetchRoleList()
})
</script>

<template>
  <div class="mt-4">
    <!-- 프로젝트별 비즈니스 데이터 권한(Role) 매핑 -->
    <CRow>
      <CCol>
        <h6 class="font-weight-bold mb-3">
          <v-icon icon="mdi-shield-key-outline" color="primary" size="sm" class="mr-2" />
          프로젝트 별 담당 권한
        </h6>

        <div v-if="!user" class="text-center py-4 text-muted border rounded bg-light">
          사용자를 선택해 주세요.
        </div>

        <div v-else-if="loading" class="text-center py-4">
          <v-progress-circular indeterminate color="primary" />
        </div>

        <div
          v-else-if="allDevProjects.length === 0"
          class="text-center py-4 text-muted border rounded bg-light"
        >
          사용 가능한 부동산 개발 프로젝트가 존재하지 않습니다.
        </div>

        <div v-else class="space-y-4">
          <CCard v-for="proj in allDevProjects" :key="proj.pk" class="mb-3">
            <CCardHeader class="bg-more-light d-flex align-items-center justify-content-between">
              <span class="fw-bold text-dark d-flex align-items-center text-body">
                <v-icon icon="mdi-folder" color="grey" size="small" class="pt-1 mr-1" />
                {{ proj.name }}
                <v-chip
                  v-if="!proj.is_public"
                  color="danger"
                  size="x-small"
                  variant="flat"
                  class="ml-2 p-2 font-weight-bold text-white"
                  density="comfortable"
                >
                  <v-icon icon="mdi-lock" size="x-small" class="mr-2" />
                  비공개
                </v-chip>
              </span>
              <v-chip size="x-small" variant="tonal" color="grey"> Business Perms</v-chip>
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol v-if="ibsRoles.length === 0" class="text-muted small">
                  시스템에 등록된 비즈니스 데이터 관련 역할([ibs_global] 카테고리)이 없습니다.
                </CCol>
                <template v-else>
                  <CCol v-for="role in ibsRoles" :key="role.pk" xs="12" sm="6" md="4" class="py-1">
                    <CFormCheck
                      :id="`member-role-${proj.pk}-${role.pk}`"
                      :label="role.name"
                      :checked="hasRole(proj.pk || 0, role.pk)"
                      :disabled="!write_auth_manage"
                      @change="toggleRole(proj.pk || 0, role.pk)"
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
