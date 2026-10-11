<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { UploadRequestOptions } from 'element-plus'
import http from '../api/http'
import Shell from '../components/Shell.vue'
import { CHANNELS, JOB_TYPES, STATUSES, statusLabel } from '../labels'

type Log = { id: number; from_status: string | null; to_status: string; changed_at: string; note: string | null }
type FileRow = { id: number; filename: string; size: number }
type App = {
  id: number
  company_name: string
  position_name: string
  job_type: string
  channel: string
  city: string | null
  salary_range: string | null
  jd_text: string | null
  status: string
  applied_at: string
  notes: string | null
  deleted_at: string | null
  logs: Log[]
}

const route = useRoute()
const router = useRouter()
const app = ref<App | null>(null)
const files = ref<FileRow[]>([])
const form = reactive({
  company_name: '',
  position_name: '',
  job_type: '',
  channel: '',
  city: '',
  salary_range: '',
  jd_text: '',
  notes: '',
  applied_at: '',
})
const changing = ref(false)
const statusForm = reactive({ to_status: '', changed_at: '', note: '' })

const id = () => Number(route.params.id)

function pad(n: number) {
  return String(n).padStart(2, '0')
}
function stamp() {
  const date = new Date()
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

async function load() {
  const { data } = await http.get(`/applications/${id()}`)
  app.value = data
  Object.assign(form, {
    company_name: data.company_name,
    position_name: data.position_name,
    job_type: data.job_type,
    channel: data.channel,
    city: data.city || '',
    salary_range: data.salary_range || '',
    jd_text: data.jd_text || '',
    notes: data.notes || '',
    applied_at: data.applied_at.slice(0, 10),
  })
  if (!data.deleted_at) {
    const filesRes = await http.get(`/applications/${id()}/attachments`)
    files.value = filesRes.data
  } else {
    files.value = []
  }
}

async function save() {
  await http.patch(`/applications/${id()}`, { ...form, applied_at: `${form.applied_at}T00:00:00` })
  await load()
}

function openStatus() {
  if (!app.value) return
  statusForm.to_status = app.value.status
  statusForm.changed_at = stamp()
  statusForm.note = ''
  changing.value = true
}

async function submitStatus() {
  await http.post(`/applications/${id()}/status`, statusForm)
  changing.value = false
  await load()
}

async function remove() {
  await http.delete(`/applications/${id()}`)
  router.push('/')
}

async function upload(option: UploadRequestOptions) {
  const body = new FormData()
  body.append('file', option.file)
  await http.post(`/applications/${id()}/attachments`, body)
  await load()
}

async function download(file: FileRow) {
  const res = await http.get(`/applications/${id()}/attachments/${file.id}`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = url
  link.download = file.filename
  link.click()
  URL.revokeObjectURL(url)
}

async function removeFile(file: FileRow) {
  await http.delete(`/applications/${id()}/attachments/${file.id}`)
  await load()
}

onMounted(load)
</script>

<template>
  <Shell v-if="app">
    <el-page-header @back="router.push('/')" content="投递详情" />
    <el-form label-width="90px" style="max-width: 640px; margin-top: 16px">
      <el-form-item label="公司"><el-input v-model="form.company_name" /></el-form-item>
      <el-form-item label="岗位"><el-input v-model="form.position_name" /></el-form-item>
      <el-form-item label="类型">
        <el-select v-model="form.job_type">
          <el-option v-for="item in JOB_TYPES" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="渠道">
        <el-select v-model="form.channel">
          <el-option v-for="item in CHANNELS" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="投递日"><el-date-picker v-model="form.applied_at" type="date" value-format="YYYY-MM-DD" /></el-form-item>
      <el-form-item label="城市"><el-input v-model="form.city" /></el-form-item>
      <el-form-item label="薪资"><el-input v-model="form.salary_range" /></el-form-item>
      <el-form-item label="JD"><el-input v-model="form.jd_text" type="textarea" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      <el-button type="primary" @click="save">保存字段</el-button>
      <el-button @click="openStatus">改状态</el-button>
      <el-button v-if="!app.deleted_at" type="danger" @click="remove">删除</el-button>
    </el-form>

    <h3>时间线</h3>
    <el-timeline>
      <el-timeline-item v-for="log in app.logs" :key="log.id" :timestamp="log.changed_at.replace('T', ' ')">
        {{ log.from_status ? statusLabel(log.from_status) + ' → ' : '' }}{{ statusLabel(log.to_status) }}
        <span v-if="log.note">（{{ log.note }}）</span>
      </el-timeline-item>
    </el-timeline>

    <template v-if="!app.deleted_at">
      <h3>附件</h3>
      <el-upload :show-file-list="false" :http-request="upload" accept=".pdf,.docx">
        <el-button>上传 pdf / docx</el-button>
      </el-upload>
      <div v-for="file in files" :key="file.id">
        {{ file.filename }}
        <el-button link @click="download(file)">下载</el-button>
        <el-button link @click="removeFile(file)">删除</el-button>
      </div>
    </template>

    <el-dialog v-model="changing" title="改状态">
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
