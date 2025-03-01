<script lang="ts" setup>
import { inject, onBeforeMount, type ComputedRef, type PropType } from 'vue'
import type { User } from '@/store/types/accounts'
import { useRoute } from 'vue-router'
import type { IssueProject, ProjectFilter } from '@/store/types/work'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
import SearchList from './SearchList.vue'
import NoData from '@/views/_Work/components/NoData.vue'

defineProps({
  projectList: { type: Array as PropType<IssueProject[]>, default: () => [] },
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const emit = defineEmits(['aside-visible', 'filter-submit'])

const workManager = inject<ComputedRef<boolean>>('workManager')
const userInfo = inject<ComputedRef<User>>('userInfo')

const route = useRoute()

const isOwnProject = (project: IssueProject) =>
  project.all_members?.map(m => m.user.pk).includes(userInfo?.value?.pk as number)

const filterSubmit = (payload: ProjectFilter) => emit('filter-submit', payload)

const hasVisible = (project: IssueProject) => {
  if (project.visible) return true
  if (project.sub_projects && project.sub_projects.length > 0)
    for (let sub of project.sub_projects) {
      if (hasVisible(sub)) return true
    }
  return false
}

onBeforeMount(() => emit('aside-visible', true))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>프로젝트</h5>
    </CCol>

    <CCol v-if="workManager" class="text-right form-text">
      <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: '프로젝트 - 추가' }" class="ml-1">새 프로젝트</router-link>
      </span>
      <span>
        <v-icon icon="mdi-cog" color="secondary" size="sm" />
        <router-link :to="{ name: '(프로젝트)' }" class="ml-1">관리</router-link>
      </span>
    </CCol>
  </CRow>

  <SearchList :all-projects="allProjects" @filter-submit="filterSubmit" />

  <NoData v-if="!projectList.length" />

  <CRow v-else>
    <template v-for="proj in projectList" :key="proj.pk">
      <CCol v-if="hasVisible(proj)" sm="12" lg="6" xl="4">
        <CCard class="my-2">
          <CCardBody class="project-set">
            <span v-if="proj.visible">
              <router-link
                :to="{ name: '(개요)', params: { projId: proj.slug } }"
                :class="{ 'text-grey': proj.status === '9' }"
              >
                {{ proj.name }}
              </router-link>
              <v-icon
                v-if="isOwnProject(proj)"
                icon="mdi-account-tag"
                color="success"
                size="15"
                class="ml-1"
              />
              <VueMarkdownIt :source="proj.description" />
            </span>

            <!-- c1 -->
            <div
              v-if="!!proj.sub_projects?.length"
              :class="{ child: proj.visible, 'project-set': !proj.visible }"
            >
              <blockquote v-for="c1 in proj.sub_projects" :key="c1.pk">
                <span v-if="c1.visible">
                  <router-link :to="{ name: '(개요)', params: { projId: c1.slug } }">
                    {{ c1.name }}
                  </router-link>
                  <v-icon
                    v-if="isOwnProject(c1)"
                    icon="mdi-account-tag"
                    color="success"
                    size="15"
                    class="ml-1"
                  />
                  <VueMarkdownIt :source="c1.description" />
                </span>

                <!-- c2 -->
                <div
                  v-if="!!c1.sub_projects?.length"
                  :class="{ child: c1.visible, 'project-set': !c1.visible }"
                >
                  <blockquote v-for="c2 in c1.sub_projects" :key="c2.pk">
                    <span v-if="c2.visible">
                      <router-link :to="{ name: '(개요)', params: { projId: c2.slug } }">
                        {{ c2.name }}
                      </router-link>
                      <v-icon
                        v-if="isOwnProject(c2)"
                        icon="mdi-account-tag"
                        color="success"
                        size="15"
                        class="ml-1"
                      />
                      <VueMarkdownIt :source="c2.description" />
                    </span>

                    <!-- c3 -->
                    <div
                      v-if="!!c2.sub_projects?.length"
                      :class="{ child: c2.visible, 'project-set': !c2.visible }"
                    >
                      <blockquote v-for="c3 in c2.sub_projects" :key="c3.pk">
                        <span v-if="c3.visible">
                          <router-link :to="{ name: '(개요)', params: { projId: c3.slug } }">
                            {{ c3.name }}
                          </router-link>
                          <v-icon
                            v-if="isOwnProject(c3)"
                            icon="mdi-account-tag"
                            color="success"
                            size="15"
                            class="ml-1"
                          />
                          <VueMarkdownIt :source="c3.description" />
                        </span>

                        <!-- c4 -->
                        <div
                          v-if="!!c3.sub_projects?.length"
                          :class="{ child: c3.visible, 'project-set': !c3.visible }"
                        >
                          <blockquote v-for="c4 in c3.sub_projects" :key="c4.pk">
                            <span v-if="c4.visible">
                              <router-link :to="{ name: '(개요)', params: { projId: c4.slug } }">
                                {{ c4.name }}
                              </router-link>
                              <v-icon
                                v-if="isOwnProject(c4)"
                                icon="mdi-account-tag"
                                color="success"
                                size="15"
                                class="ml-1"
                              />
                              <VueMarkdownIt :source="c4.description" />
                            </span>

                            <!-- c5 -->
                            <div
                              v-if="!!c4.sub_projects?.length"
                              :class="{ child: c4.visible, 'project-set': !c4.visible }"
                            >
                              <blockquote v-for="c5 in c4.sub_projects" :key="c5.pk">
                                <span v-if="c5.visible">
                                  <router-link
                                    :to="{ name: '(개요)', params: { projId: c5.slug } }"
                                  >
                                    {{ c5.name }}
                                  </router-link>
                                  <v-icon
                                    v-if="isOwnProject(c5)"
                                    icon="mdi-account-tag"
                                    color="success"
                                    size="15"
                                    class="ml-1"
                                  />
                                  <VueMarkdownIt :source="c5.description" />
                                </span>
                              </blockquote>
                            </div>
                          </blockquote>
                        </div>
                      </blockquote>
                    </div>
                  </blockquote>
                </div>
              </blockquote>
            </div>
          </CCardBody>
        </CCard>
      </CCol>
    </template>
  </CRow>

  <CRow>
    <CCol class="text-right form-text">
      <span class="mr-2">
        <v-icon icon="mdi-account-tag" color="success" size="15" class="mr-1" />
        <span class="mt-2">내 프로젝트</span>
      </span>

      <span>
        <v-icon icon="mdi-bookmark" color="info" size="15" class="mr-1" />
        <span class="mt-2">내 북마크</span>
      </span>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.project-set {
  padding-bottom: 0;
}

.project-set a {
  font-weight: bold;
  font-size: 1.13em;
}

.project-set .child {
  a {
    font-size: 0.96em;
    font-weight: normal;
  }

  padding-left: 12px;
  border-left: 3px solid #ddd;
}
</style>
