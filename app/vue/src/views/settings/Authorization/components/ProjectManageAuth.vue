<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { write_auth_manage } from '@/utils/pageAuth'
import { useWork } from '@/store/pinia/work_project'
import { useAccount } from '@/store/pinia/account'
import { bgLight } from '@/utils/cssMixins'
import api from '@/api'
import Multiselect from '@vueform/multiselect'

const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['get-allowed'])

const workStore = useWork()
const accountStore = useAccount()

const allowedProjects = ref<number[]>([])
const assignedProject = ref<number | null>(null)
const memberList = ref<any[]>([]) // 사용자의 전체 Member 레코드 목록
const loading = ref(false)

const isInActive = computed(() => !props.user || loading.value)
const getProjects = computed(() =>
  workStore.allReadableProjects.map(p => ({ value: p.pk, label: p.name })),
)
const getAssigneds = computed(() =>
  getProjects.value.filter(p => allowedProjects.value.includes(p.value ?? 0)),
)

// 사용자의 Member 목록 및 프로젝트 바인딩 초기화
const fetchUserProjectState = async () => {
  if (!props.user?.pk) {
    allowedProjects.value = []
    assignedProject.value = null
    memberList.value = []
    return
  }
  
  loading.value = true
  try {
    // 1. 사용자의 모든 Member 조회
    const members = await workStore.fetchMemberList(props.user.pk)
    if (members) {
      memberList.value = members
      allowedProjects.value = members.map((m: any) => m.project.pk)
    }
    
    // 2. 사용자의 메인 프로젝트(default_project) 설정 바인딩
    assignedProject.value = props.user.default_project || null
  } catch (error) {
    console.error('Failed to load user project permissions:', error)
  } finally {
    loading.value = false
  }
}

watch(
  () => props.user,
  () => fetchUserProjectState(),
  { immediate: true },
)

// 프로젝트가 선택기로 추가됨
const handleProjectAdd = async (projPk: any) => {
  if (loading.value || !props.user?.pk) return
  
  // 이미 해당 멤버가 있는 프로젝트인지 이중 확인
  const isExist = memberList.value.some(m => m.project.pk === projPk)
  if (isExist) return

  // workStore.allReadableProjects에서 프로젝트 객체 탐색하여 slug 획득
  const proj = workStore.allReadableProjects.find(p => p.pk === projPk)
  if (!proj?.slug) return

  // 기본 역할 지정 (work_core 카테고리 역할 중 정렬 우선순위가 높은 역할 선택)
  const defaultRole = workStore.roleList.find(r => (r.category || 'work_core') === 'work_core')
  const rolePk = defaultRole ? defaultRole.pk : 1

  try {
    loading.value = true
    await workStore.createMember({
      project: projPk,
      slug: proj.slug,
      user_id: props.user.pk,
      role_ids: [rolePk],
    } as any)
  } catch (e) {
    console.error('Failed to create project member:', e)
  } finally {
    // 상태값 리로드 및 부모 컴포넌트에 통보
    await fetchUserProjectState()
    emit('get-allowed', allowedProjects.value)
  }
}

// 프로젝트가 선택기에서 제거됨
const handleProjectRemove = async (projPk: any) => {
  if (loading.value || !props.user?.pk) return

  const targetMember = memberList.value.find(m => m.project.pk === projPk)
  if (!targetMember) return

  try {
    loading.value = true
    await workStore.deleteMember(targetMember.pk)
  } catch (e) {
    console.error('Failed to delete project member:', e)
  } finally {
    // 상태값 리로드 및 부모 컴포넌트에 통보
    await fetchUserProjectState()
    emit('get-allowed', allowedProjects.value)
  }
}

// 담당 메인 프로젝트 변경 (User 모델 업데이트)
const handleAssignedChange = async (newVal: number | null) => {
  if (!props.user?.pk) return
  
  try {
    // API를 통해 사용자의 default_project 변경
    await api.patch(`/user/${props.user.pk}/`, {
      default_project: newVal,
    })
    
    // 로컬 스토어 캐시 갱신
    await accountStore.fetchUser(props.user.pk)
  } catch (error) {
    console.error('Failed to update default project:', error)
  }
}

onMounted(() => {
  workStore.fetchAllProjectList()
  workStore.fetchRoleList()
})
</script>

<template>
  <CCallout color="secondary" :class="bgLight" class="mt-1">
    <CRow>
      <CCol md="10" lg="8" xl="6">
        <CRow class="m-1">
          <CFormLabel class="col-md-4 col-form-label"> 허용 프로젝트</CFormLabel>
          <CCol>
            <Multiselect
              v-model="allowedProjects"
              :options="getProjects"
              placeholder="프로젝트"
              mode="tags"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              :disabled="isInActive || !write_auth_manage"
              @select="handleProjectAdd"
              @deselect="handleProjectRemove"
            />
            <small class="form-text">
              사용자가 조회 및 관리할 수 있는 프로젝트들을 선택하여 멤버로 등록합니다.
            </small>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="10" lg="8" xl="6">
        <CRow class="m-1">
          <CFormLabel class="col-md-4 col-form-label"> 담당 메인 프로젝트</CFormLabel>
          <CCol>
            <Multiselect
              v-model="assignedProject"
              :options="getAssigneds"
              placeholder="프로젝트"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              :disabled="isInActive || allowedProjects.length === 0"
              @change="handleAssignedChange"
            />
            <small class="form-text">
              사용자의 각 화면에서 선택한 프로젝트를 기본 프로젝트로 보여줍니다.
            </small>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>
</template>
