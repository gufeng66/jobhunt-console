<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import Shell from '../components/Shell.vue'
import { CHANNELS, JOB_TYPES, STATUSES, statusLabel } from '../labels'

type Row = {
  id: number
  company_name: string
  position_name: string
  job_type: string
  channel: string
  status: string
  applied_at: string
  last_status_at: string
}

const router = useRouter()
const rows = ref<Row[]>([])
const total = ref(0)
const page = ref(1)
const deleted = ref(false)
const filters = reactive({ status: '', job_type: '', channel: '', q: '' })
const creating = ref(false)
const statusOf = ref<Row | null>(null)
const createForm = reactive(blankCreate())
const statusForm = reactive({ to_status: 'interview', changed_at: stamp(), note: '' })

function pad(n: number) {
  return String(n).padStart(2, '0')
}
function stamp(date = new Date()) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
function blankCreate() {
  return {
    company_name: '',
    position_name: '',
    job_type: '',
    channel: 'BOSS',
    status: 'communicated',
    applied_at: stamp().slice(0, 10),
    status_at: stamp(),
    city: '',
    salary_range: '',
    notes: '',
  }
}

async function load() {
  const { data } = await http.get('/applications', {
    params: {
      page: page.value,
      deleted: deleted.value ? 1 : 0,
      status: filters.status || undefined,
      job_type: filters.job_type || undefined,
      channel: filters.channel || undefined,
      q: filters.q || undefined,
    },
  })
  rows.value = data.items
  total.value = data.total
}

function openCreate() {
  Object.assign(createForm, blankCreate())
  creating.value = true
}

async function submitCreate() {
  await http.post('/applications', {
    ...createForm,
    applied_at: `${createForm.applied_at}T00:00:00`,
    status_at: createForm.status === 'communicated' ? undefined : createForm.status_at,
  })
  creating.value = false
  await load()
}

function openStatus(row: Row) {
  statusOf.value = row
  statusForm.to_status = row.status
  statusForm.changed_at = stamp()
  statusForm.note = ''
}

async function submitStatus() {
  if (!statusOf.value) return
  await http.post(`/applications/${statusOf.value.id}/status`, statusForm)
  statusOf.value = null
  await load()
}

async function restore(row: Row) {
  await http.post(`/applications/${row.id}/restore`)
  await load()
}

onMounted(load)
</script>

<template>
  <Shell>
    <el-form inline>
      <el-select v-model="filters.status" clearable placeholder="状态" style="width: 120px">
        <el-option v-for="item in STATUSES" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filters.job_type" clearable placeholder="类型" style="width: 110px">
        <el-option v-for="item in JOB_TYPES" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="filters.channel" clearable placeholder="渠道" style="width: 110px">
        <el-option v-for="item in CHANNELS" :key="item" :label="item" :value="item" />
      </el-select>
      <el-input v-model="filters.q" placeholder="公司或岗位" clearable style="width: 180px" />
      <el-button @click="page = 1; load()">查询</el-button>
      <el-checkbox v-model="deleted" @change="page = 1; load()">只看已删除</el-checkbox>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </el-form>
    <el-table :data="rows">
      <el-table-column prop="company_name" label="公司" />
      <el-table-column prop="position_name" label="岗位" />
      <el-table-column prop="job_type" label="类型" width="80" />
      <el-table-column prop="channel" label="渠道" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="投递日" width="120">
        <template #default="{ row }">{{ row.applied_at.slice(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link @click="router.push(`/applications/${row.id}`)">详情</el-button>
          <el-button v-if="!deleted" link @click="openStatus(row)">改状态</el-button>
          <el-button v-else link @click="restore(row)">恢复</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      layout="prev, pager, next"
      :total="total"
      :page-size="20"
      :current-page="page"
      @current-change="(value: number) => { page = value; load() }"
    />

    <el-dialog v-model="creating" title="新建投递">
      <el-form label-width="90px">
        <el-form-item label="公司"><el-input v-model="createForm.company_name" /></el-form-item>
        <el-form-item label="岗位"><el-input v-model="createForm.position_name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="createForm.job_type" placeholder="必选">
            <el-option v-for="item in JOB_TYPES" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="createForm.channel">
            <el-option v-for="item in CHANNELS" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="createForm.status">
            <el-option v-for="item in STATUSES" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="投递日"><el-date-picker v-model="createForm.applied_at" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item v-if="createForm.status !== 'communicated'" label="状态时间">
          <el-date-picker v-model="createForm.status_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="城市"><el-input v-model="createForm.city" /></el-form-item>
        <el-form-item label="薪资"><el-input v-model="createForm.salary_range" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="createForm.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog :model-value="!!statusOf" title="改状态" @close="statusOf = null">
      <el-form label-width="90px">
        <el-form-item label="状态">
          <el-select v-model="statusForm.to_status">
            <el-option v-for="item in STATUSES" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="statusForm.changed_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="statusForm.note" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitStatus">保存</el-button>
      </template>
    </el-dialog>
  </Shell>
</template>
