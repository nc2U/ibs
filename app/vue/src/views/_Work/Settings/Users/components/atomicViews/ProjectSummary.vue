<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins'

defineProps({
  issueProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const route = useRoute()
const userId = computed(() => route.params.userId)

const getMember = (members: any[]) => {
  let member = members.filter(m => m.user.pk == userId.value)[0]
  return member ? [member.roles, member.created] : [[], '1900-01-01']
}
</script>

<template>
  <CRow class="mb-3">
    <CCol>
      <v-divider class="mb-0" />
      <CTable small striped hover responsive>
        <CTableHead class="text-center">
          <CTableRow>
            <CTableHeaderCell>프로젝트</CTableHeaderCell>
            <CTableHeaderCell>역할</CTableHeaderCell>
            <CTableHeaderCell class="text-center">등록시각</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <template v-for="proj in issueProjects" :key="proj.pk">
            <CTableRow>
              <CTableDataCell class="text-left">
                <router-link :to="{ name: '(개요)', params: { projId: proj.slug } }">
                  {{ proj.name }}
                </router-link>
              </CTableDataCell>
              <CTableDataCell>
                {{
                  getMember(proj.all_members ?? [])[0]
                    .map((r: any) => r.name)
                    .join(', ')
                }}
              </CTableDataCell>
              <CTableDataCell class="text-center">
                {{ dateFormat(getMember(proj.all_members ?? [])[1], '/') }}
              </CTableDataCell>
            </CTableRow>

            <template v-for="subs1 in proj.sub_projects" :key="subs1.pk">
              <CTableRow>
                <CTableDataCell>
                  <v-icon
                    icon="mdi-chevron-right"
                    color="secondary"
                    :class="`ml-${subs1.depth - 1}`"
                  />
                  <router-link :to="{ name: '(개요)', params: { projId: subs1.slug } }">
                    {{ subs1.name }}
                  </router-link>
                </CTableDataCell>
                <CTableDataCell>
                  {{
                    getMember(subs1.all_members ?? [])[0]
                      .map((r: any) => r.name)
                      .join(', ')
                  }}
                </CTableDataCell>
                <CTableDataCell class="text-center">
                  {{ dateFormat(getMember(subs1.all_members ?? [])[1], '/') }}
                </CTableDataCell>
              </CTableRow>
              <template v-for="subs2 in subs1.sub_projects" :key="subs2.pk">
                <CTableRow>
                  <CTableDataCell>
                    <v-icon
                      icon="mdi-chevron-right"
                      color="secondary"
                      :class="`ml-${subs2.depth - 1}`"
                    />
                    <router-link :to="{ name: '(개요)', params: { projId: subs2.slug } }">
                      {{ subs2.name }}
                    </router-link>
                  </CTableDataCell>
                  <CTableDataCell>
                    {{
                      getMember(subs2.all_members ?? [])[0]
                        .map((r: any) => r.name)
                        .join(', ')
                    }}
                  </CTableDataCell>
                  <CTableDataCell class="text-center">
                    {{ dateFormat(getMember(subs2.all_members ?? [])[1], '/') }}
                  </CTableDataCell>
                </CTableRow>
                <template v-for="subs3 in subs2.sub_projects" :key="subs3.pk">
                  <CTableRow>
                    <CTableDataCell>
                      <v-icon
                        icon="mdi-chevron-right"
                        color="secondary"
                        :class="`ml-${subs3.depth - 1}`"
                      />
                      <router-link :to="{ name: '(개요)', params: { projId: subs3.slug } }">
                        {{ subs3.name }}
                      </router-link>
                    </CTableDataCell>
                    <CTableDataCell>
                      {{
                        getMember(subs3.all_members ?? [])[0]
                          .map((r: any) => r.name)
                          .join(', ')
                      }}
                    </CTableDataCell>
                    <CTableDataCell class="text-center">
                      {{ dateFormat(getMember(subs3.all_members ?? [])[1], '/') }}
                    </CTableDataCell>
                  </CTableRow>
                  <template v-for="subs4 in subs3.sub_projects" :key="subs4.pk">
                    <CTableRow>
                      <CTableDataCell>
                        <v-icon
                          icon="mdi-chevron-right"
                          color="secondary"
                          :class="`ml-${subs4.depth - 1}`"
                        />
                        <router-link :to="{ name: '(개요)', params: { projId: subs4.slug } }">
                          {{ subs4.name }}
                        </router-link>
                      </CTableDataCell>
                      <CTableDataCell>
                        {{
                          getMember(subs4.all_members ?? [])[0]
                            .map((r: any) => r.name)
                            .join(', ')
                        }}
                      </CTableDataCell>
                      <CTableDataCell class="text-center">
                        {{ dateFormat(getMember(subs4.all_members ?? [])[1], '/') }}
                      </CTableDataCell>
                    </CTableRow>
                    <template v-for="subs5 in subs4.sub_projects" :key="subs5.pk">
                      <CTableRow>
                        <CTableDataCell>
                          <v-icon
                            icon="mdi-chevron-right"
                            color="secondary"
                            :class="`ml-${subs5.depth - 1}`"
                          />
                          <router-link :to="{ name: '(개요)', params: { projId: subs5.slug } }">
                            {{ subs5.name }}
                          </router-link>
                        </CTableDataCell>
                        <CTableDataCell>
                          {{
                            getMember(subs5.all_members ?? [])[0]
                              .map((r: any) => r.name)
                              .join(', ')
                          }}
                        </CTableDataCell>
                        <CTableDataCell class="text-center">
                          {{ dateFormat(getMember(subs5.all_members ?? [])[1], '/') }}
                        </CTableDataCell>
                      </CTableRow>
                    </template>
                  </template>
                </template>
              </template>
            </template>
          </template>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
