import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Loader2, Trash2, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { apiAuth } from '@/shared/lib/api'
import { formatDate } from '@/shared/lib/utils'

const CSV_COLUMNS: { key: string; label: string }[] = [
  { key: 'nome_aluno',      label: 'Aluno' },
  { key: 'matricula',       label: 'Matrícula' },
  { key: 'email',           label: 'E-mail' },
  { key: 'telefone',        label: 'Telefone' },
  { key: 'turma',           label: 'Turma' },
  { key: 'orientador',      label: 'Orientador' },
  { key: 'coorientador',    label: 'Coorientador' },
  { key: 'titulo_trabalho', label: 'Título do Trabalho' },
  { key: 'modalidade',      label: 'Modalidade' },
  { key: 'resumo',          label: 'Resumo' },
  { key: 'palavra_chave',   label: 'Palavras-chave' },
  { key: 'membro_banca1',   label: 'Membro Banca 1' },
  { key: 'membro_banca2',   label: 'Membro Banca 2' },
  { key: 'membro_banca3',   label: 'Membro Banca 3' },
  { key: 'data_defesa',     label: 'Data de Defesa' },
  { key: 'horario_defesa',  label: 'Horário' },
  { key: 'local_defesa',    label: 'Local' },
  { key: 'status',          label: 'Status' },
  { key: 'submission_date', label: 'Data de Envio' },
]

function downloadCSV(rows: Row[]) {
  const escape = (v: string) => `"${(v ?? '').replace(/"/g, '""')}"`
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

type Row = Record<string, string>

function unique(rows: Row[], key: string): string[] {
  return Array.from(new Set(rows.map(r => r[key] ?? '').filter(Boolean))).sort()
}

export function ConsultaRequerimentoTCC() {
  const queryClient = useQueryClient()
  const [filtroOrientador, setFiltroOrientador] = useState('')
  const [filtroModalidade, setFiltroModalidade] = useState('')
  const [filtroDataDe, setFiltroDataDe] = useState('')
  const [filtroDataAte, setFiltroDataAte] = useState('')
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [deleting, setDeleting] = useState(false)
  const [gerandoAtaId, setGerandoAtaId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['requerimento-tcc-list'],
    queryFn: async () => (await apiAuth.get('/api/v1/requerimento-tcc?por_pagina=200')).data,
  })

  const rows: Row[] = Array.isArray(data) ? data : (data?.items ?? [])

  const filtered = useMemo(() => {
    return rows.filter(r => {
      if (filtroOrientador && r.orientador !== filtroOrientador) return false
      if (filtroModalidade && r.modalidade !== filtroModalidade) return false
      if (filtroDataDe && r.data_defesa && r.data_defesa < filtroDataDe) return false
      if (filtroDataAte && r.data_defesa && r.data_defesa > filtroDataAte) return false
      return true
    })
  }, [rows, filtroOrientador, filtroModalidade, filtroDataDe, filtroDataAte])

  const hasFilters = filtroOrientador || filtroModalidade || filtroDataDe || filtroDataAte

  const allFilteredIds = filtered.map(r => Number(r.id))
  const allSelected = allFilteredIds.length > 0 && allFilteredIds.every(id => selected.has(id))
  const someSelected = allFilteredIds.some(id => selected.has(id))

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
      await Promise.all(
        [...selected].map(id => apiAuth.delete(`/api/v1/requerimento-tcc/${id}`))
      )
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
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Erro ao gerar ATA')
    } finally {
      setGerandoAtaId(null)
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

      {!isLoading && filtered.length === 0 && (
        <div className="fasi-info-box">Nenhum requerimento encontrado.</div>
      )}

      {filtered.length > 0 && (
        <div className="fasi-card overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-foreground">
              {filtered.length} registro{filtered.length !== 1 ? 's' : ''}
              {hasFilters && rows.length !== filtered.length && ` (de ${rows.length} total)`}
            </span>
            <div className="flex items-center gap-2">
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
                onClick={() => downloadCSV(filtered)}
                className="fasi-btn-outline py-1 px-3 text-sm flex items-center gap-1.5"
              >
                <Download className="w-4 h-4" />
                Baixar CSV
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
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
                  {['Aluno', 'Matrícula', 'Orientador', 'Título', 'Modalidade', 'Defesa', 'Ações'].map(h => (
                    <th key={h} className="px-3 py-2.5 text-left font-medium whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => {
                  const id = Number(r.id)
                  const isSelected = selected.has(id)
                  return (
                    <tr key={i}
                      className={isSelected ? 'bg-fasi-50' : (i % 2 === 0 ? 'bg-white' : 'bg-fasi-50/30')}
                      onClick={() => toggleRow(id)}
                    >
                      <td className="px-3 py-2 cursor-pointer" onClick={e => { e.stopPropagation(); toggleRow(id) }}>
                        <input type="checkbox" checked={isSelected} onChange={() => toggleRow(id)} className="cursor-pointer" />
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">{r.nome_aluno}</td>
                      <td className="px-3 py-2">{r.matricula}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{r.orientador}</td>
                      <td className="px-3 py-2 max-w-[200px] truncate" title={r.titulo_trabalho}>{r.titulo_trabalho}</td>
                      <td className="px-3 py-2">{r.modalidade}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{r.data_defesa ? formatDate(r.data_defesa) : '—'}</td>
                      <td className="px-3 py-2" onClick={e => e.stopPropagation()}>
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
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PageShell>
  )
}
