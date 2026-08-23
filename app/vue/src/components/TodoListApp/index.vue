<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import type { Todo as T } from '@/store/types/accounts'
import Todo from './Todo.vue'

const todos = ref<T[]>([])
const visibility = ref('all')

type filterType = {
  [key: string]: (x: T[]) => ((y: T) => boolean) | T[]
}

const account = useAccount()
const userInfo = computed(() => account.userInfo?.pk || 1)
const myTodos = computed(() => account.myTodos)
watch(myTodos, val => (todos.value = val))

const filters: filterType = {
  all: (myTodos: T[]) => myTodos,
  active: (myTodos: T[]) => myTodos.filter(todo => !todo.completed),
  completed: (myTodos: T[]) => myTodos.filter(todo => todo.completed),
}

const allChecked = computed(() => myTodos.value.every(todo => todo.completed))

const filteredTodos = computed(() => filters[visibility.value](todos.value))

const remaining = computed(() => todos.value.filter((todo: T) => !todo.completed).length)

const addTodo = (e: Event) => {
  const title = (e.target as HTMLInputElement).value.trim()
  if (userInfo.value && title) {
    account.createTodo({ user: userInfo.value, title })
  }
  ;(e.target as HTMLInputElement).value = ''
}

const toggleTodo = (todo: T) => {
  todo.completed = !todo.completed
  const payload = { pk: todo.pk, completed: todo.completed }
  account.patchTodo(payload)
}

const delTodo = (pk: number) => {
  const soft_deleted = true
  const payload = { pk, soft_deleted }
  account.patchTodo(payload)
}

const editTodo = (pk: number, title: string) => {
  const payload = { pk, title }
  account.patchTodo(payload)
}

const clearCompleted = () => {
  todos.value.forEach((todo: T) => {
    if (todo.completed) {
      const payload = { pk: todo.pk, soft_deleted: true }
      account.patchTodo(payload)
    }
  })
}

const toggleAll = ({ completed }: { completed: boolean }) => {
  todos.value.forEach((todo: T) => {
    todo.completed = completed
    const payload = { pk: todo.pk, completed: todo.completed }
    account.patchTodo(payload)
  })
}

const pluralize = (n: number, w: string) => (n === 1 ? w : w + 's')
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

onBeforeMount(() => account.fetchTodoList())
</script>

<template>
  <section class="todoapp mb-4">
    <!-- header -->
    <header class="header">
      <input
        class="new-todo"
        autofocus
        autocomplete="off"
        placeholder="여기에 할 일을 메모 하세요."
        @keyup.enter="addTodo"
      />
    </header>
    <!-- main section -->
    <section v-show="todos.length" class="main">
      <input
        id="toggle-all"
        :checked="allChecked"
        class="toggle-all"
        type="checkbox"
        @change="toggleAll({ completed: !allChecked })"
      />
      <label for="toggle-all" />
      <ul class="todo-list">
        <Todo
          v-for="todo in filteredTodos as T[]"
          :key="todo.pk"
          :todo="todo"
          @toggle-todo="toggleTodo"
          @edit-todo="editTodo"
          @del-todo="delTodo"
        />
      </ul>
    </section>
    <!-- footer -->
    <footer v-show="todos.length" class="footer">
      <span class="todo-count">
        <strong>{{ remaining }}</strong> {{ pluralize(remaining, 'item') }} left
      </span>
      <ul class="filters">
        <li v-for="(val, key) in filters" :key="key">
          <a :class="{ selected: visibility === key }" @click.prevent="visibility = key as string">
            {{ capitalize(key as string) }}
          </a>
        </li>
      </ul>

      <button v-show="todos.length > remaining" class="clear-completed" @click="clearCompleted">
        Clear completed
      </button>
    </footer>
  </section>

  <footer class="info text-center bottom-footer" style="font-size: 0.875rem">
    <p v-if="todos.length">할 일 목록을 수정하려면 더블클릭 하세요.</p>
    <p v-else>첫 번째 할 일 목록을 메모해 보세요.</p>
  </footer>
</template>

<style lang="scss">
@import 'index';

.bottom-footer {
  color: #ccc;
}

.dark-theme {
  .bottom-footer {
    color: #3e4853;
  }
}
</style>
