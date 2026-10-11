<script setup lang="ts">
import { onMounted, ref } from 'vue'
import http from '../api/http'
import Shell from '../components/Shell.vue'

type Stats = {
  total: number
  resume_requested: number
  interview: number
  offered: number
  rejected: number
  withdrawn: number
  average_days: number | null
  trend: { week: string; count: number }[]
}

const jobType = ref('')
const stats = ref<Stats | null>(null)

async function load() {
  const { data } = await http.get('/stats', { params: { job_type: jobType.value || undefined } })
  stats.value = data
}

function ratio(count: number) {
  if (!stats.value || stats.value.total === 0) return '0%'
  return `${Math.round((count / stats.value.total) * 100)}%`
}

onMounted(load)
</script>

<template>
  <Shell>
    <el-radio-group v-model="jobType" @change="load">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="实习">实习</el-radio-button>
      <el-radio-button value="校招">校招</el-radio-button>
    </el-radio-group>
    <div v-if="stats" class="funnel">
      <p>已投递 {{ stats.total }}（100%）</p>
      <p>要简历 {{ stats.resume_requested }}（{{ ratio(stats.resume_requested) }}）</p>
      <p>面试 {{ stats.interview }}（{{ ratio(stats.interview) }}）</p>
      <p>录用 {{ stats.offered }}（{{ ratio(stats.offered) }}）</p>
      <p>拒绝 {{ stats.rejected }}　已放弃 {{ stats.withdrawn }}</p>
      <p>到达 offer 平均 {{ stats.average_days === null ? '—' : stats.average_days + ' 天' }}</p>
    </div>
    <el-table v-if="stats" :data="stats.trend">
      <el-table-column prop="week" label="周一开始" />
      <el-table-column prop="count" label="新增" />
    </el-table>
  </Shell>
</template>

<style scoped>
.funnel {
  margin: 16px 0;
}
</style>
