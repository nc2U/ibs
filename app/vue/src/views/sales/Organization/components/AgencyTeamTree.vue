<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SalesAgency, SalesTeam } from '@/store/types/sales'

const props = defineProps({
  project: { type: Number, required: true },
  selectedTeamId: { type: Number as PropType<number | null>, default: null },
  selectedAgencyId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits([
  'select-team',
  'select-agency',
  'add-agency',
  'edit-agency',
  'add-team',
  'edit-team',
])

const salesStore = useSales()
const agencyList = computed(() => salesStore.agencyList)
const teamList = computed(() => salesStore.teamList)

const getTeamsForAgency = (agencyId: number) =>
  teamList.value.filter(t => t.agency === agencyId)

const selectAgency = (agency: SalesAgency) => {
  emit('select-agency', agency.id)
}

const selectTeam = (team: SalesTeam) => {
  emit('select-team', team.id)
}

const deleteAgency = async (agency: SalesAgency) => {
  if (confirm(`'${agency.name}' 대행사를 삭제하시겠습니까?\n(하위 조직 및 인력이 함께 삭제되거나 오류가 발생할 수 있습니다)`)) {
    await salesStore.deleteAgency(agency.id)
    if (props.project) {
      await salesStore.fetchAgencyList(props.project)
      await salesStore.fetchTeamList(undefined, props.project)
    }
  }
}

const deleteTeam = async (team: SalesTeam) => {
  if (confirm(`'${team.name}' 조직을 삭제하시겠습니까?`)) {
    await salesStore.deleteTeam(team.id)
    if (props.project) {
      await salesStore.fetchTeamList(undefined, props.project)
    }
  }
}
</script>

<template>
  <CCard class="mb-4 shadow-sm">
    <CCardHeader class="d-flex justify-content-between align-items-center bg-light">
      <div class="fw-bold">
        <v-icon icon="mdi-sitemap" size="small" class="mr-1 text-primary" />
        영업 조직 체계
      </div>
      <v-btn color="primary" size="x-small" variant="tonal" @click="emit('add-agency')">
        <v-icon icon="mdi-plus" size="x-small" class="mr-1" />
        대행사 추가
      </v-btn>
    </CCardHeader>

    <CCardBody class="p-2">
      <!-- 전체 보기 선택 -->
      <div
        class="tree-item p-2 mb-2 rounded cursor-pointer d-flex justify-content-between align-items-center"
        :class="{ 'bg-primary text-white': !selectedAgencyId && !selectedTeamId, 'bg-body-secondary': selectedAgencyId || selectedTeamId }"
        @click="emit('select-team', null)"
      >
        <span class="fw-bold">
          <v-icon icon="mdi-account-group" size="small" class="mr-1" />
          전체 인력 보기
        </span>
        <CBadge color="secondary" shape="rounded-pill">전체</CBadge>
      </div>

      <!-- 대행사가 없는 경우 -->
      <div v-if="agencyList.length === 0" class="py-4 text-center text-muted small">
        등록된 분양 대행사가 없습니다.<br />
        상단의 [대행사 추가]를 눌러 등록하세요.
      </div>

      <!-- 대행사 및 팀 목록 -->
      <div v-for="agency in agencyList" :key="agency.id" class="agency-block mb-3 border rounded p-2">
        <div class="d-flex justify-content-between align-items-center mb-2 pb-1 border-bottom">
          <div
            class="fw-bold cursor-pointer text-truncate"
            :class="{ 'text-primary': selectedAgencyId === agency.id }"
            @click="selectAgency(agency)"
          >
            <CBadge :color="agency.is_direct_managed ? 'info' : 'warning'" class="mr-1">
              {{ agency.is_direct_managed ? '직영' : '외주' }}
            </CBadge>
            {{ agency.name }}
          </div>
          <div>
            <v-btn icon="mdi-pencil" size="x-small" variant="text" color="secondary" @click.stop="emit('edit-agency', agency)" />
            <v-btn icon="mdi-delete" size="x-small" variant="text" color="danger" @click.stop="deleteAgency(agency)" />
            <v-btn icon="mdi-plus-box" size="x-small" variant="text" color="primary" title="팀 추가" @click.stop="emit('add-team', agency.id)" />
          </div>
        </div>

        <!-- 하위 팀 목록 -->
        <div class="team-list pl-2">
          <div
            v-for="team in getTeamsForAgency(agency.id)"
            :key="team.id"
            class="team-item py-1 px-2 mb-1 rounded cursor-pointer d-flex justify-content-between align-items-center"
            :class="{ 'bg-primary text-white': selectedTeamId === team.id, 'hover-bg': selectedTeamId !== team.id }"
            @click="selectTeam(team)"
          >
            <span class="small text-truncate">
              <v-icon icon="mdi-subdirectory-arrow-right" size="x-small" class="mr-1 opacity-75" />
              <span v-if="team.parent_name" class="opacity-75">{{ team.parent_name }} &gt; </span>
              <strong>{{ team.name }}</strong>
            </span>
            <div class="d-flex align-items-center">
              <CBadge color="light" text-color="dark" class="mr-1" shape="rounded-pill">
                {{ team.members_count ?? 0 }}명
              </CBadge>
              <v-btn
                icon="mdi-pencil"
                size="x-small"
                variant="text"
                :color="selectedTeamId === team.id ? 'white' : 'secondary'"
                @click.stop="emit('edit-team', team)"
              />
              <v-btn
                icon="mdi-close"
                size="x-small"
                variant="text"
                :color="selectedTeamId === team.id ? 'white' : 'danger'"
                @click.stop="deleteTeam(team)"
              />
            </div>
          </div>

          <div v-if="getTeamsForAgency(agency.id).length === 0" class="small text-muted pl-3 py-1">
            등록된 팀이 없습니다.
          </div>
        </div>
      </div>
    </CCardBody>
  </CCard>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.hover-bg:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
