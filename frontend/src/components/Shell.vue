<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const router = useRouter()
const auth = useAuth()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <el-container>
    <el-header class="bar">
      <strong>求职作战台</strong>
      <el-button link @click="router.push('/')">投递</el-button>
      <el-button link @click="router.push('/dashboard')">看板</el-button>
      <el-button link class="out" @click="logout">退出</el-button>
    </el-header>
    <el-main><slot /></el-main>
  </el-container>
</template>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--el-border-color);
}
.out {
  margin-left: auto;
}
</style>
