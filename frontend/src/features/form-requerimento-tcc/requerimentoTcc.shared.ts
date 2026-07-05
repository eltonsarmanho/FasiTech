import { z } from 'zod'

import { ANO_MSG, ANO_REGEX, EMAIL_MSG, MATRICULA_MSG, MATRICULA_REGEX } from '@/shared/lib/masks'

export const requerimentoTccSchema = z.object({
  nome_aluno: z.string().min(3, 'Nome obrigatório'),
  matricula: z.string().regex(MATRICULA_REGEX, MATRICULA_MSG),
  email: z.string().email(EMAIL_MSG),
  telefone: z.string().optional(),
  turma: z.string().regex(ANO_REGEX, ANO_MSG),
  orientador: z.string().min(1, 'Orientador obrigatório'),
  coorientador: z.string().optional(),
  titulo_trabalho: z.string().min(3, 'Título obrigatório'),
  resumo: z.string().min(10, 'Resumo obrigatório'),
  palavra_chave: z.string().min(1, 'Palavras-chave obrigatórias'),
  modalidade: z.string().min(1, 'Modalidade obrigatória'),
  membro_banca1: z.string().min(1, 'Membro 1 obrigatório'),
  membro_banca2: z.string().min(1, 'Membro 2 obrigatório'),
  membro_banca3: z.string().optional(),
  data_defesa: z.string().min(1, 'Data de defesa obrigatória'),
  horario_defesa: z.string().regex(/^\d{1,2}:\d{2}$/, 'Use o formato HH:MM (ex: 14:30)'),
  local_defesa: z.string().optional(),
})

export type RequerimentoTccFormData = z.infer<typeof requerimentoTccSchema>

export interface RequerimentoTccRecord {
  id: number
  nome_aluno: string
  matricula: string
  email: string
  telefone: string | null
  turma: string
  orientador: string
  coorientador: string | null
  titulo_trabalho: string
  resumo: string | null
  palavra_chave: string | null
  modalidade: string
  membro_banca1: string | null
  membro_banca2: string | null
  membro_banca3: string | null
  data_defesa: string | null
  horario_defesa: string | null
  local_defesa: string | null
  status?: string
  submission_date?: string | null
}

export const requerimentoTccDefaultValues: RequerimentoTccFormData = {
  nome_aluno: '',
  matricula: '',
  email: '',
  telefone: '',
  turma: '',
  orientador: '',
  coorientador: '',
  titulo_trabalho: '',
  resumo: '',
  palavra_chave: '',
  modalidade: '',
  membro_banca1: '',
  membro_banca2: '',
  membro_banca3: 'Nenhum',
  data_defesa: '',
  horario_defesa: '',
  local_defesa: '',
}

export function normalizeRequerimentoTccPayload(data: RequerimentoTccFormData) {
  return {
    ...data,
    membro_banca3: data.membro_banca3 === 'Nenhum' || !data.membro_banca3 ? '' : data.membro_banca3,
  }
}

export function requerimentoTccRecordToFormValues(
  record: RequerimentoTccRecord | null | undefined,
): RequerimentoTccFormData {
  if (!record) return requerimentoTccDefaultValues

  return {
    nome_aluno: record.nome_aluno ?? '',
    matricula: record.matricula ?? '',
    email: record.email ?? '',
    telefone: record.telefone ?? '',
    turma: record.turma ?? '',
    orientador: record.orientador ?? '',
    coorientador: record.coorientador ?? '',
    titulo_trabalho: record.titulo_trabalho ?? '',
    resumo: record.resumo ?? '',
    palavra_chave: record.palavra_chave ?? '',
    modalidade: record.modalidade ?? '',
    membro_banca1: record.membro_banca1 ?? '',
    membro_banca2: record.membro_banca2 ?? '',
    membro_banca3: record.membro_banca3 ?? 'Nenhum',
    data_defesa: record.data_defesa ?? '',
    horario_defesa: record.horario_defesa ?? '',
    local_defesa: record.local_defesa ?? '',
  }
}
