import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Loader2, Trash2, FileText, PencilLine, X, ArrowDown, ArrowUp, ArrowUpDown, Send } from 'lucide-react'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { apiAuth } from '@/shared/lib/api'
import { formatDate } from '@/shared/lib/utils'
import { useFuncionarios, nomesFiltrados } from '@/shared/hooks/useFuncionarios'
import { usePeriodosSubmissao, isPeriodoAtivo, formatPeriodo } from '@/shared/hooks/usePeriodosSubmissao'
import {
  normalizeRequerimentoTccPayload,
  requerimentoTccRecordToFormValues,
  requerimentoTccSchema,
  type RequerimentoTccFormData,
  type RequerimentoTccRecord,
} from '@/features/form-requerimento-tcc/requerimentoTcc.shared'
import { RequerimentoTccFields } from '@/features/form-requerimento-tcc/RequerimentoTccFields'

type CsvColumnKey = Exclude<keyof RequerimentoTccRecord, 'id'>

const CSV_COLUMNS: { key: CsvColumnKey; label: string }[] = [
  { key: 'nome_aluno', label: 'Aluno' },
  { key: 'matricula', label: 'Matrícula' },
  { key: 'email', label: 'E-mail' },
  { key: 'telefone', label: 'Telefone' },
  { key: 'turma', label: 'Turma' },
  { key: 'orientador', label: 'Orientador' },
  { key: 'coorientador', label: 'Coorientador' },
  { key: 'titulo_trabalho', label: 'Título do Trabalho' },
  { key: 'modalidade', label: 'Modalidade' },
  { key: 'resumo', label: 'Resumo' },
  { key: 'palavra_chave', label: 'Palavras-chave' },
  { key: 'membro_banca1', label: 'Membro Banca 1' },
  { key: 'membro_banca2', label: 'Membro Banca 2' },
  { key: 'membro_banca3', label: 'Membro Banca 3' },
  { key: 'data_defesa', label: 'Data de Defesa' },
  { key: 'horario_defesa', label: 'Horário' },
  { key: 'local_defesa', label: 'Local' },
  { key: 'status', label: 'Status' },
  { key: 'submission_date', label: 'Data de Envio' },
]

type ApiListResponse = {
  total: number
  pagina: number
  por_pagina: number
  items: RequerimentoTccRecord[]
}

type SortField = 'nome_aluno' | 'orientador' | 'data_defesa'
type SortDirection = 'asc' | 'desc'

function compareDateStrings(a: string | null | undefined, b: string | null | undefined) {
  if (!a && !b) return 0
  if (!a) return 1
  if (!b) return -1
  return a.localeCompare(b)
}

function compareText(a: string | null | undefined, b: string | null | undefined) {
  return (a ?? '').localeCompare(b ?? '', 'pt-BR', { sensitivity: 'base' })
}

function SortIcon({ active, direction }: { active: boolean; direction: SortDirection }) {
  if (!active) return <ArrowUpDown className="w-3.5 h-3.5 opacity-70" />
  return direction === 'asc'
    ? <ArrowUp className="w-3.5 h-3.5" />
    : <ArrowDown className="w-3.5 h-3.5" />
}

function downloadCSV(rows: RequerimentoTccRecord[]) {
  const escape = (v: string | null | undefined) => `"${(v ?? '').replace(/"/g, '""')}"`
  const header = CSV_COLUMNS.map(c => escape(c.label)).join(',')
  const body = rows.map(r =>
    CSV_COLUMNS.map(c => escape(r[c.key] ?? '')).join(',')
  ).join('\n')
  const blob = new Blob(['﻿' + header + '\n' + body], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `requerimento-tcc-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function unique(rows: RequerimentoTccRecord[], key: keyof RequerimentoTccRecord): string[] {
  return Array.from(new Set(rows.map(r => String(r[key] ?? '')).filter(Boolean))).sort()
}

function getApiErrorMessage(err: unknown, fallback: string) {
  const detail = (err as any)?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first?.msg === 'string') return first.msg
  }
  return (err as any)?.message || fallback
}

function getApiErrorDetail(err: unknown) {
  return (err as any)?.response?.data?.detail
}

function getApiErrorStatus(err: unknown) {
  return (err as any)?.response?.status
}

function RequerimentoTccEditor({
  record,
  onClose,
  onSaved,
}: {
  record: RequerimentoTccRecord
  onClose: () => void
  onSaved: () => void
}) {
  const { data: periodosDefesa = [] } = usePeriodosSubmissao('tcc')
  const { data: funcionarios = [] } = useFuncionarios()
  const orientadores = nomesFiltrados(funcionarios, f => f.categoria === 'Docente' && f.tipo === 'Interno')
  const membrosBanca = nomesFiltrados(funcionarios, f => f.categoria === 'Docente')

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<RequerimentoTccFormData>({
    resolver: zodResolver(requerimentoTccSchema),
    defaultValues: requerimentoTccRecordToFormValues(record),
  })

  useEffect(() => {
    reset(requerimentoTccRecordToFormValues(record))
  }, [record, reset])

  const dataDefesaValue = watch('data_defesa')
  const [conflictErrors, setConflictErrors] = useState<string[]>([])

  const updateMutation = useMutation({
    mutationFn: async (data: RequerimentoTccFormData) => {
      if (periodosDefesa.length > 0 && data.data_defesa && !isPeriodoAtivo(periodosDefesa, data.data_defesa)) {
        const detalhes = periodosDefesa.map(p => `Período ${p.numero}: ${formatPeriodo(p)}`).join(' | ')
        throw new Error(`A data de defesa está fora dos períodos permitidos. Períodos: ${detalhes}`)
      }
      const payload = normalizeRequerimentoTccPayload(data)
      try {
        return await apiAuth.put(`/api/v1/requerimento-tcc/${record.id}`, payload)
      } catch (err: unknown) {
        if (getApiErrorStatus(err) === 405) {
          if (payload.matricula !== record.matricula) {
            throw new Error(
              'O backend atual nao suporta atualizar matricula por esta tela. Tente novamente sem alterar a matricula ou reinicie o backend atualizado.'
            )
          }
          return apiAuth.post('/api/v1/forms/requerimento-tcc', payload)
        }
        throw err
      }
    },
    onSuccess: () => {
      setConflictErrors([])
      toast.success('Requerimento atualizado com sucesso!')
      onSaved()
    },
    onError: (err: unknown) => {
      setConflictErrors([])
      const detail = getApiErrorDetail(err) as { type?: string; conflitos?: string[] } | undefined
      if (detail?.type === 'cruzamento_horario' && Array.isArray(detail.conflitos)) {
        setConflictErrors(detail.conflitos)
        return
      }
      toast.error(getApiErrorMessage(err, 'Erro ao atualizar. Tente novamente.'))
    },
  })

  return (
    <FormSection title="Editar registro selecionado">
      <div className="mb-4 flex items-start justify-between gap-3 rounded-lg border border-fasi-200 bg-fasi-50 p-4">
        <div>
          <p className="text-sm font-semibold text-foreground">{record.nome_aluno}</p>
          <p className="text-xs text-muted-foreground">
            Matrícula {record.matricula} · Defesa {record.data_defesa ? formatDate(record.data_defesa) : 'sem data'}
          </p>
        </div>
        <button type="button" className="fasi-btn-outline py-1 px-3 text-xs" onClick={onClose}>
          <X className="w-3.5 h-3.5" />
          Limpar seleção
        </button>
      </div>

      <form onSubmit={handleSubmit(data => updateMutation.mutate(data))} noValidate>
        <RequerimentoTccFields
          register={register}
          errors={errors}
          orientadores={orientadores}
          membrosBanca={membrosBanca}
          periodosDefesa={periodosDefesa}
          dataDefesaValue={dataDefesaValue}
        />

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="fasi-btn-primary w-full sm:w-auto"
          >
            {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <PencilLine className="w-4 h-4" />}
            {updateMutation.isPending ? 'Salvando...' : 'Salvar alterações'}
          </button>
          <button type="button" onClick={onClose} className="fasi-btn-secondary w-full sm:w-auto">
            Cancelar edição
          </button>
        </div>

        {conflictErrors.length > 0 && (
          <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4">
            <p className="flex items-center gap-2 font-semibold text-red-700 mb-2">
              <span>⚠️</span> Conflito de horário detectado
            </p>
            <ul className="space-y-1.5 text-sm text-red-700">
              {conflictErrors.map((msg, i) => (
                <li key={i} className="flex gap-2">
                  <span className="mt-0.5 shrink-0">•</span>
                  <span>{msg}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-red-600">
              Ajuste a data e/ou horário da defesa para evitar o conflito antes de salvar novamente.
            </p>
          </div>
        )}
      </form>
    </FormSection>
  )
}

export function ConsultaRequerimentoTCC() {
  const queryClient = useQueryClient()
  const [filtroOrientador, setFiltroOrientador] = useState('')
  const [filtroModalidade, setFiltroModalidade] = useState('')
  const [filtroDataDe, setFiltroDataDe] = useState('')
  const [filtroDataAte, setFiltroDataAte] = useState('')
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null)
  const [confirmAtaLote, setConfirmAtaLote] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [gerandoAtaId, setGerandoAtaId] = useState<number | null>(null)
  const [gerandoAtaLote, setGerandoAtaLote] = useState(false)
  const [sortField, setSortField] = useState<SortField>('data_defesa')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const { data, isLoading } = useQuery<ApiListResponse | RequerimentoTccRecord[]>({
    queryKey: ['requerimento-tcc-list'],
    queryFn: async () => (await apiAuth.get('/api/v1/requerimento-tcc?por_pagina=200')).data,
  })

  const rows: RequerimentoTccRecord[] = Array.isArray(data) ? data : (data?.items ?? [])

  const filtered = useMemo(() => {
    return rows.filter(r => {
      if (filtroOrientador && r.orientador !== filtroOrientador) return false
      if (filtroModalidade && r.modalidade !== filtroModalidade) return false
      if (filtroDataDe && r.data_defesa && r.data_defesa < filtroDataDe) return false
      if (filtroDataAte && r.data_defesa && r.data_defesa > filtroDataAte) return false
      return true
    })
  }, [rows, filtroOrientador, filtroModalidade, filtroDataDe, filtroDataAte])

  const sorted = useMemo(() => {
    const next = [...filtered]
    next.sort((a, b) => {
      let result = 0
      if (sortField === 'nome_aluno') result = compareText(a.nome_aluno, b.nome_aluno)
      if (sortField === 'orientador') result = compareText(a.orientador, b.orientador)
      if (sortField === 'data_defesa') result = compareDateStrings(a.data_defesa, b.data_defesa)
      return sortDirection === 'asc' ? result : -result
    })
    return next
  }, [filtered, sortDirection, sortField])

  const hasFilters = filtroOrientador || filtroModalidade || filtroDataDe || filtroDataAte

  const selectedRecord = useMemo(
    () => rows.find(r => r.id === selectedRecordId) ?? null,
    [rows, selectedRecordId],
  )
  const selectedRows = useMemo(
    () => sorted.filter(r => selected.has(r.id)),
    [selected, sorted],
  )
  const selectedOrientadores = useMemo(() => {
    const counts = new Map<string, number>()
    selectedRows.forEach(row => {
      const key = row.orientador || 'Nao informado'
      counts.set(key, (counts.get(key) ?? 0) + 1)
    })
    return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0], 'pt-BR', { sensitivity: 'base' }))
  }, [selectedRows])

  const allFilteredIds = sorted.map(r => r.id)
  const allSelected = allFilteredIds.length > 0 && allFilteredIds.every(id => selected.has(id))
  const someSelected = allFilteredIds.some(id => selected.has(id))

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
      return
    }
    setSortField(field)
    setSortDirection('asc')
  }

  function toggleRow(id: number) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (allSelected) {
      setSelected(prev => {
        const next = new Set(prev)
        allFilteredIds.forEach(id => next.delete(id))
        return next
      })
    } else {
      setSelected(prev => new Set([...prev, ...allFilteredIds]))
    }
  }

  async function handleDeleteSelected() {
    if (!window.confirm(`Confirma a exclusão de ${selected.size} registro(s)? Esta ação não pode ser desfeita.`)) return
    setDeleting(true)
    try {
      await Promise.all([...selected].map(id => apiAuth.delete(`/api/v1/requerimento-tcc/${id}`)))
      if (selectedRecordId && selected.has(selectedRecordId)) {
        setSelectedRecordId(null)
      }
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ['requerimento-tcc-list'] })
    } finally {
      setDeleting(false)
    }
  }

  async function handleGerarAta(id: number) {
    setGerandoAtaId(id)
    try {
      const res = await apiAuth.post(`/api/v1/requerimento-tcc/${id}/gerar-ata`)
      toast.success(res.data?.message || 'ATA gerada e enviada ao orientador!')
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, 'Erro ao gerar ATA'))
    } finally {
      setGerandoAtaId(null)
    }
  }

  async function handleGerarAtaLote() {
    const ids = [...selected]
    if (ids.length === 0) return

    setGerandoAtaLote(true)
    try {
      const { data } = await apiAuth.post('/api/v1/requerimento-tcc/gerar-ata-lote', {
        submission_ids: ids,
      })

      const enviados = Number(data?.enviados?.length ?? 0)
      const falhas = Number(data?.falhas?.length ?? 0)

      if (enviados > 0 && falhas === 0) {
        toast.success(`${enviados} e-mail(s) de ATA enviado(s) com sucesso!`)
      } else if (enviados > 0) {
        toast.success(`${enviados} ATA(s) enviada(s) e ${falhas} falha(s).`)
      } else {
        toast.error(data?.message || 'Nenhum e-mail de ATA foi enviado.')
      }

      if (falhas > 0) {
        const detalhes = (data?.falhas ?? [])
          .slice(0, 3)
          .map((item: { id: number; detail: string }) => `#${item.id}: ${item.detail}`)
          .join(' | ')
        if (detalhes) {
          toast.error(`Falhas no lote: ${detalhes}`)
        }
      }
      setConfirmAtaLote(false)
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, 'Erro ao disparar ATA em lote'))
    } finally {
      setGerandoAtaLote(false)
    }
  }

  return (
    <PageShell icon="📋" title="Consulta Requerimento TCC"
      subtitle="Dados submetidos no formulário de Requerimento TCC">

      <FormSection title="Filtros">
        <FieldGroup cols={2}>
          <Field label="Orientador">
            <select className="fasi-input" value={filtroOrientador}
              onChange={e => setFiltroOrientador(e.target.value)}>
              <option value="">Todos</option>
              {unique(rows, 'orientador').map(o => <option key={o}>{o}</option>)}
            </select>
          </Field>
          <Field label="Modalidade">
            <select className="fasi-input" value={filtroModalidade}
              onChange={e => setFiltroModalidade(e.target.value)}>
              <option value="">Todas</option>
              {unique(rows, 'modalidade').map(m => <option key={m}>{m}</option>)}
            </select>
          </Field>
          <Field label="Data de defesa — de">
            <input type="date" className="fasi-input" value={filtroDataDe}
              onChange={e => setFiltroDataDe(e.target.value)} />
          </Field>
          <Field label="Data de defesa — até">
            <input type="date" className="fasi-input" value={filtroDataAte}
              onChange={e => setFiltroDataAte(e.target.value)} />
          </Field>
        </FieldGroup>
        {hasFilters && (
          <button className="fasi-btn-outline mt-3 py-1 px-3 text-sm"
            onClick={() => { setFiltroOrientador(''); setFiltroModalidade(''); setFiltroDataDe(''); setFiltroDataAte('') }}>
            Limpar filtros
          </button>
        )}
      </FormSection>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-fasi-500" />
        </div>
      )}

      {!isLoading && sorted.length === 0 && (
        <div className="fasi-info-box">Nenhum requerimento encontrado.</div>
      )}

      {sorted.length > 0 && (
        <div className="fasi-card overflow-hidden">
          <div className="p-4 border-b border-border flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <span className="text-sm font-semibold text-foreground">
              {sorted.length} registro{sorted.length !== 1 ? 's' : ''}
              {hasFilters && rows.length !== sorted.length && ` (de ${rows.length} total)`}
            </span>
            <div className="flex items-center gap-2 flex-wrap">
              {selectedRecord && (
                <button
                  onClick={() => setSelectedRecordId(null)}
                  className="fasi-btn-outline py-1 px-3 text-sm"
                >
                  <X className="w-4 h-4" />
                  Limpar seleção
                </button>
              )}
              {someSelected && (
                <button
                  onClick={() => setConfirmAtaLote(true)}
                  disabled={gerandoAtaLote}
                  className="fasi-btn-outline py-1 px-3 text-sm flex items-center gap-1.5 text-blue-700 border-blue-300 hover:bg-blue-50"
                >
                  {gerandoAtaLote
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Send className="w-4 h-4" />}
                  {gerandoAtaLote
                    ? `Disparando ${selected.size}...`
                    : `Disparar ATA ${selected.size !== 1 ? `(${selected.size})` : ''}`}
                </button>
              )}
              {someSelected && (
                <button
                  onClick={handleDeleteSelected}
                  disabled={deleting}
                  className="fasi-btn-outline py-1 px-3 text-sm flex items-center gap-1.5 text-red-600 border-red-300 hover:bg-red-50"
                >
                  {deleting
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Trash2 className="w-4 h-4" />}
                  Excluir {selected.size} selecionado{selected.size !== 1 ? 's' : ''}
                </button>
              )}
              <button
                onClick={() => downloadCSV(sorted)}
                className="fasi-btn-outline py-1 px-3 text-sm flex items-center gap-1.5"
              >
                <Download className="w-4 h-4" />
                Baixar CSV
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full table-fixed text-sm">
              <thead>
                <tr className="bg-fasi-500 text-white">
                  <th className="px-3 py-2.5 w-10">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={el => { if (el) el.indeterminate = someSelected && !allSelected }}
                      onChange={toggleAll}
                      className="cursor-pointer"
                    />
                  </th>
                  <th className="px-3 py-2.5 w-10 whitespace-nowrap">Sel.</th>
                  <th className="w-[16%] px-3 py-2.5 text-left font-medium whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => handleSort('nome_aluno')}
                      className="inline-flex items-center gap-1 font-medium hover:text-blue-100"
                    >
                      Aluno
                      <SortIcon active={sortField === 'nome_aluno'} direction={sortDirection} />
                    </button>
                  </th>
                  <th className="w-[11%] px-3 py-2.5 text-left font-medium whitespace-nowrap">Matrícula</th>
                  <th className="w-[18%] px-3 py-2.5 text-left font-medium whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => handleSort('orientador')}
                      className="inline-flex items-center gap-1 font-medium hover:text-blue-100"
                    >
                      Orientador
                      <SortIcon active={sortField === 'orientador'} direction={sortDirection} />
                    </button>
                  </th>
                  <th className="w-[18%] px-3 py-2.5 text-left font-medium whitespace-nowrap">Título</th>
                  <th className="w-[12%] px-3 py-2.5 text-left font-medium whitespace-nowrap">Modalidade</th>
                  <th className="w-[8%] px-3 py-2.5 text-left font-medium whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => handleSort('data_defesa')}
                      className="inline-flex items-center gap-1 font-medium hover:text-blue-100"
                    >
                      Defesa
                      <SortIcon active={sortField === 'data_defesa'} direction={sortDirection} />
                    </button>
                  </th>
                  <th className="w-[17%] px-3 py-2.5 text-left font-medium whitespace-nowrap">Ações</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((r, i) => {
                  const id = r.id
                  const isSelected = selected.has(id)
                  const isActive = selectedRecordId === id
                  return (
                    <tr
                      key={id}
                      className={
                        isActive
                          ? 'bg-blue-50 ring-1 ring-inset ring-blue-200'
                          : (isSelected ? 'bg-fasi-50' : (i % 2 === 0 ? 'bg-white' : 'bg-fasi-50/30'))
                      }
                      onClick={() => setSelectedRecordId(id)}
                    >
                      <td className="px-3 py-2 cursor-pointer" onClick={e => { e.stopPropagation(); toggleRow(id) }}>
                        <input type="checkbox" checked={isSelected} onChange={() => toggleRow(id)} className="cursor-pointer" />
                      </td>
                      <td className="px-3 py-2 cursor-pointer" onClick={e => { e.stopPropagation(); setSelectedRecordId(id) }}>
                        <input
                          type="radio"
                          name="requerimento-tcc-selecionado"
                          checked={isActive}
                          onChange={() => setSelectedRecordId(id)}
                          className="cursor-pointer"
                        />
                      </td>
                      <td className="px-3 py-2 truncate" title={r.nome_aluno}>{r.nome_aluno}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{r.matricula}</td>
                      <td className="px-3 py-2 truncate" title={r.orientador}>{r.orientador}</td>
                      <td className="px-3 py-2 truncate" title={r.titulo_trabalho}>{r.titulo_trabalho}</td>
                      <td className="px-3 py-2 truncate" title={r.modalidade}>{r.modalidade}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{r.data_defesa ? formatDate(r.data_defesa) : '—'}</td>
                      <td className="px-3 py-2" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-2 flex-wrap">
                          <button
                            onClick={() => setSelectedRecordId(id)}
                            className={`fasi-btn-outline py-1 px-2 text-xs flex items-center gap-1 whitespace-nowrap ${
                              isActive ? 'border-blue-300 bg-blue-50 text-blue-700' : ''
                            }`}
                          >
                            <PencilLine className="w-3 h-3" />
                            {isActive ? 'Selecionado' : 'Editar'}
                          </button>
                          <button
                            onClick={() => handleGerarAta(id)}
                            disabled={gerandoAtaId === id}
                            title="Gerar ATA de Defesa e enviar ao orientador"
                            className="fasi-btn-outline py-1 px-2 text-xs flex items-center gap-1 whitespace-nowrap"
                          >
                            {gerandoAtaId === id
                              ? <Loader2 className="w-3 h-3 animate-spin" />
                              : <FileText className="w-3 h-3" />}
                            {gerandoAtaId === id ? 'Gerando...' : 'Gerar ATA'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedRecord && (
        <div className="mt-6">
          <RequerimentoTccEditor
            record={selectedRecord}
            onClose={() => setSelectedRecordId(null)}
            onSaved={() => {
              queryClient.invalidateQueries({ queryKey: ['requerimento-tcc-list'] })
            }}
          />
        </div>
      )}

      {confirmAtaLote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="fasi-card w-full max-w-2xl mx-4 p-6">
            <div className="flex items-start justify-between gap-4 mb-5">
              <div>
                <h3 className="text-lg font-semibold text-foreground">Confirmar disparo em lote</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Sera enviado 1 e-mail por registro selecionado, com processamento individual de cada ATA.
                </p>
              </div>
              <button
                type="button"
                onClick={() => !gerandoAtaLote && setConfirmAtaLote(false)}
                className="fasi-btn-outline py-1 px-2 text-xs"
                disabled={gerandoAtaLote}
              >
                <X className="w-3.5 h-3.5" />
                Fechar
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
              <div className="rounded-lg border border-border bg-background px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Registros</p>
                <p className="text-2xl font-bold text-foreground">{selectedRows.length}</p>
              </div>
              <div className="rounded-lg border border-border bg-background px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Orientadores</p>
                <p className="text-2xl font-bold text-foreground">{selectedOrientadores.length}</p>
              </div>
              <div className="rounded-lg border border-border bg-background px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">E-mails previstos</p>
                <p className="text-2xl font-bold text-foreground">{selectedRows.length}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
              <div className="rounded-lg border border-border p-4 bg-white">
                <p className="text-sm font-semibold text-foreground mb-3">Orientadores no lote</p>
                <div className="space-y-2 max-h-56 overflow-auto">
                  {selectedOrientadores.map(([nome, total]) => (
                    <div key={nome} className="flex items-center justify-between text-sm border-b border-border/70 pb-2 last:border-b-0 last:pb-0">
                      <span className="truncate pr-3" title={nome}>{nome}</span>
                      <span className="text-muted-foreground whitespace-nowrap">{total} registro{total !== 1 ? 's' : ''}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-border p-4 bg-white">
                <p className="text-sm font-semibold text-foreground mb-3">Primeiros registros selecionados</p>
                <div className="space-y-2 max-h-56 overflow-auto">
                  {selectedRows.slice(0, 8).map(row => (
                    <div key={row.id} className="text-sm border-b border-border/70 pb-2 last:border-b-0 last:pb-0">
                      <p className="font-medium truncate" title={row.nome_aluno}>{row.nome_aluno}</p>
                      <p className="text-muted-foreground text-xs truncate" title={row.orientador}>
                        {row.orientador} · {row.data_defesa ? formatDate(row.data_defesa) : 'Sem data'}
                      </p>
                    </div>
                  ))}
                  {selectedRows.length > 8 && (
                    <p className="text-xs text-muted-foreground">
                      E mais {selectedRows.length - 8} registro(s) no lote.
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row justify-end gap-3">
              <button
                type="button"
                onClick={() => setConfirmAtaLote(false)}
                disabled={gerandoAtaLote}
                className="fasi-btn-secondary"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleGerarAtaLote}
                disabled={gerandoAtaLote || selectedRows.length === 0}
                className="fasi-btn-primary"
              >
                {gerandoAtaLote ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {gerandoAtaLote ? 'Disparando...' : `Confirmar envio de ${selectedRows.length} ATA(s)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  )
}
