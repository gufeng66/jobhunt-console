export const STATUSES = [
  { value: 'communicated', label: '仅沟通' },
  { value: 'resume_requested', label: '要简历' },
  { value: 'interview', label: '面试' },
  { value: 'offered', label: '录用' },
  { value: 'rejected', label: '拒绝' },
  { value: 'withdrawn', label: '已放弃' },
]

export const JOB_TYPES = ['实习', '校招']
export const CHANNELS = ['BOSS', '官网', '内推', '其他']

export function statusLabel(code: string) {
  return STATUSES.find((item) => item.value === code)?.label ?? code
}
