<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../stores/auth'

const router = useRouter()
const auth = useAuth()
const form = reactive({ username: 'admin', password: '' })
const dbNow = ref('')

onMounted(async () => {
  if (auth.token) router.replace('/')
  const res = await fetch('/api/health')
  if (res.ok) dbNow.value = (await res.json()).now
})

async function submit() {
  const { data } = await http.post('/auth/login', form)
  auth.setToken(data.access_token)
  router.push('/')
}
</script>

<template>
  <el-card class="card">
    <h1>求职作战台</h1>
    <p v-if="dbNow">数据库时间：{{ dbNow }}</p>
    <el-form @submit.prevent="submit">
      <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
      <el-button type="primary" native-type="submit">登录</el-button>
    </el-form>
  </el-card>
</template>

<style scoped>
.card {
  max-width: 420px;
  margin: 80px auto;
}
</style>
