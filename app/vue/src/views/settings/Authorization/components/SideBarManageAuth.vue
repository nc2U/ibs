<script lang="ts" setup>
import { ref, computed, onMounted, watch, type PropType } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import type { User } from '@/store/types/accounts'
import type { Role, Member } from '@/store/types/work_project'
import { write_auth_manage } from '@/utils/pageAuth'
import ProjectManageAuth from './ProjectManageAuth.vue'

const props = defineProps({
  user: { type: Object as PropType<User | null>, default: null },
  allowed: { type: Array as PropType<number[]>, default: () => [] },
})

const emit = defineEmits(['get-allowed', 'get-assigned'])

const workStore = useWork()
const roleList = computed<Role[]>(() => workStore.roleList)

// ibs_global 카테고리의 역할 목록 필터링
const ibsRoles = computed(() => roleList.value.filter(r => r.category === 'ibs_global'))

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
    // workStore 또는 API를 직접 호출해 사용자의 프로젝트 멤버 리스트 조회
    // Member API 엔드포인트: /api/v1/member/?user={user_id}
    const response = await workStore.fetchMemberList({ user: props.user.pk })
    if (response) {
      memberList.value = response
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
  { immediate: true }
)

const getAllowed = (payload: number[]) => {
  emit('get-allowed', payload)
  // 허용 프로젝트가 변경되면 멤버 리스트 갱신
  setTimeout(() => fetchUserMembers(), 500)
}

const getAssigned = (payload: number | null) => emit('get-assigned', payload)

// 멤버의 역할 보유 여부 확인
const hasRole = (member: Member, rolePk: number) => {
  return member.roles.some(r => r.pk === rolePk)
}

// 멤버의 역할 토글 및 업데이트
const toggleRole = async (member: Member, rolePk: number) => {
  if (!write_auth_manage.value) return
  
  const currentRolePks = member.roles.map(r => r.pk)
  const index = currentRolePks.indexOf(rolePk)
  
  if (index === -1) {
    currentRolePks.push(rolePk)
  } else {
    currentRolePks.splice(index, 1)
  }

  try {
    await workStore.patchMember({
      pk: member.pk,
      roles: currentRolePks,
    })
    // 갱신을 위해 재로드
    await fetchUserMembers()
  } catch (error) {
    console.error('Failed to update member role:', error)
  }
}

onMounted(() => {
  workStore.fetchRoleList()
})
</script>

<template>
  <div class="mt-4">
    <!-- 프로젝트 할당 영역 -->
    <CRow>
      <CCol>
        <h6 class="font-weight-bold mb-3">
          <v-icon icon="mdi-sitemap" color="success" size="sm" class="mr-2" />
          허용 프로젝트 설정
        </h6>
      </CCol>
    </CRow>

    <ProjectManageAuth
      :user="user as User"
      @get-allowed="getAllowed"
      @get-assigned="getAssigned"
    />

    <v-divider class="my-4" />

    <!-- 프로젝트별 비즈니스 데이터 권한(Role) 매핑 -->
    <CRow>
      <CCol>
        <h6 class="font-weight-bold mb-3">
          <v-icon icon="mdi-shield-key-outline" color="primary" size="sm" class="mr-2" />
          프로젝트별 비즈니스 권한 (ibs_global 역할 매핑)
        </h6>
        
        <div v-if="!user" class="text-center py-4 text-muted border rounded bg-light">
          사용자를 선택해 주세요.
        </div>
        
        <div v-else-if="loading" class="text-center py-4">
          <v-progress-circular indeterminate color="primary" />
        </div>
        
        <div v-else-if="memberList.length === 0" class="text-center py-4 text-muted border rounded bg-light">
          할당된 프로젝트가 없습니다. 위의 '허용 프로젝트 설정'에서 프로젝트를 먼저 허용해 주세요.
        </div>

        <div v-else class="space-y-4">
          <CCard v-for="mem in memberList" :key="mem.pk" class="mb-3">
            <CCardHeader class="bg-light d-flex align-items-center justify-content-between">
              <span class="fw-bold text-dark">
                <v-icon icon="mdi-folder-outline" size="small" class="mr-1" />
                {{ mem.project.name }}
              </span>
              <span class="badge bg-secondary">Project Assignment</span>
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol v-if="ibsRoles.length === 0" class="text-muted small">
                  시스템에 등록된 비즈니스 데이터 역할([ibs_global] 카테고리)이 없습니다.
                </CCol>
                <template v-else>
                  <CCol
                    v-for="role in ibsRoles"
                    :key="role.pk"
                    xs="12"
                    sm="6"
                    md="4"
                    class="py-1"
                  >
                    <CFormCheck
                      :id="`member-role-${mem.pk}-${role.pk}`"
                      :label="role.name"
                      :checked="hasRole(mem, role.pk)"
                      :disabled="!write_auth_manage"
                      @change="toggleRole(mem, role.pk)"
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
