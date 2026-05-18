import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Download } from 'lucide-react'
import { PageShell } from '@/shared/components/PageShell'
import { apiAuth } from '@/shared/lib/api'
import { formatDate } from '@/shared/lib/utils' // usado no exportCSV

type Projeto = {
  id: number
  docente: string
  nome_projeto: string
  natureza: string
  edital: string
  ano_edital: string
  solicitacao: string
  carga_horaria: string
  parecerista1: string
  parecerista2: string
  status: string
  submission_date: string
}

const STATUS_OPTIONS = ['recebido', 'iniciado', 'cancelado', 'terminado'] as const

const STATUS_STYLE: Record<string, string> = {
  recebido: 'bg-blue-50 text-blue-700 border-blue-200',
  iniciado: 'bg-amber-50 text-amber-700 border-amber-200',
  cancelado: 'bg-red-50 text-red-700 border-red-200',
  terminado: 'bg-green-50 text-green-700 border-green-200',
}

function statusStyle(s: string) {
  return STATUS_STYLE[s] ?? 'bg-fasi-50 text-fasi-700 border-fasi-200'
}

function exportCSV(rows: Projeto[]) {
  const headers = ['Docente', 'Projeto', 'Natureza', 'Edital', 'Ano', 'Solicitação',
    'Carga Horária', 'Parecerista 1', 'Parecerista 2', 'Enviado em', 'Status']
  const body = rows.map(r => [
    r.docente, r.nome_projeto, r.natureza, r.edital, r.ano_edital,
    r.solicitacao, r.carga_horaria, r.parecerista1, r.parecerista2,
    r.submission_date ? formatDate(r.submission_date) : '',
    r.status ?? 'recebido',
  ])
  const csv = [headers, ...body]
    .map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `projetos_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="fasi-card p-4 border-l-4 border-fasi-500">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-fasi-600 mt-1">{value}</p>
    </div>
  )
}

function FilterSelect({
  label, value, onChange, options,
}: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-muted-foreground">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground
                   focus:outline-none focus:ring-2 focus:ring-fasi-400 focus:border-transparent"
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}

export function ConsultaProjetos() {
  const queryClient = useQueryClient()
  const [filterDocente, setFilterDocente] = useState('Todos')
  const [filterNatureza, setFilterNatureza] = useState('Todas')
  const [filterAno, setFilterAno] = useState('Todos')
  const [filterStatus, setFilterStatus] = useState('Todos')

  const { data, isLoading } = useQuery({
    queryKey: ['projetos-list'],
    queryFn: async () => (await apiAuth.get('/api/v1/projetos?por_pagina=1000')).data,
  })

  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) =>
      apiAuth.patch(`/api/v1/projetos/${id}/status`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projetos-list'] }),
  })

  const allRows: Projeto[] = data?.items ?? []

  const docentes = useMemo(() => {
    const unique = [...new Set(allRows.map(r => r.docente).filter(Boolean))].sort()
    return ['Todos', ...unique]
  }, [allRows])

  const naturezas = useMemo(() => {
    const unique = [...new Set(allRows.map(r => r.natureza).filter(Boolean))].sort()
    return ['Todas', ...unique]
  }, [allRows])

  const anos = useMemo(() => {
    const unique = [...new Set(
      allRows.map(r => r.ano_edital).filter(v => v && v !== 'N/C' && v !== 'S/D')
    )].sort().reverse()
    return ['Todos', ...unique]
  }, [allRows])

  const rows = useMemo(() => {
    return allRows.filter(r => {
      if (filterDocente !== 'Todos' && r.docente !== filterDocente) return false
      if (filterNatureza !== 'Todas' && r.natureza !== filterNatureza) return false
      if (filterAno !== 'Todos' && r.ano_edital !== filterAno) return false
      if (filterStatus !== 'Todos' && (r.status ?? 'recebido') !== filterStatus) return false
      return true
    })
  }, [allRows, filterDocente, filterNatureza, filterAno, filterStatus])

  const countNatureza = (term: string) =>
    rows.filter(r => r.natureza?.toLowerCase().includes(term)).length

  const hasFilters = filterDocente !== 'Todos' || filterNatureza !== 'Todas'
    || filterAno !== 'Todos' || filterStatus !== 'Todos'

  return (
    <PageShell icon="📊" title="Consulta — Projetos Docentes"
      subtitle="Projetos de Ensino, Pesquisa e Extensão submetidos pelos docentes">

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-fasi-500" />
        </div>
      )}

      {!isLoading && allRows.length > 0 && (
        <>
          {/* Métricas */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <MetricCard label="Total de Projetos" value={rows.length} />
            <MetricCard label="Extensão" value={countNatureza('extens')} />
            <MetricCard label="Pesquisa" value={countNatureza('pesquisa')} />
            <MetricCard label="Ensino" value={countNatureza('ensino')} />
          </div>

          {/* Filtros */}
          <div className="fasi-card p-4 mb-4">
            <p className="text-sm font-semibold text-foreground mb-3">🔍 Filtros</p>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <FilterSelect label="Docente" value={filterDocente} onChange={setFilterDocente} options={docentes} />
              <FilterSelect label="Natureza" value={filterNatureza} onChange={setFilterNatureza} options={naturezas} />
              <FilterSelect label="Ano do Edital" value={filterAno} onChange={setFilterAno} options={anos} />
              <FilterSelect
                label="Status"
                value={filterStatus}
                onChange={setFilterStatus}
                options={['Todos', ...STATUS_OPTIONS]}
              />
            </div>
            {hasFilters && (
              <button
                onClick={() => {
                  setFilterDocente('Todos')
                  setFilterNatureza('Todas')
                  setFilterAno('Todos')
                  setFilterStatus('Todos')
                }}
                className="mt-3 text-xs text-fasi-600 hover:text-fasi-700 underline"
              >
                Limpar filtros
              </button>
            )}
          </div>

          {/* Tabela */}
          {rows.length === 0 ? (
            <div className="fasi-info-box">Nenhum projeto encontrado com os filtros aplicados.</div>
          ) : (
            <div className="fasi-card overflow-hidden">
              <div className="p-4 border-b border-border flex items-center justify-between">
                <span className="text-sm font-semibold text-foreground">
                  {rows.length} projeto{rows.length !== 1 ? 's' : ''}
                </span>
                <div className="flex items-center gap-3">
                  {hasFilters && (
                    <span className="text-xs text-muted-foreground">de {allRows.length} no total</span>
                  )}
                  <button
                    onClick={() => exportCSV(rows)}
                    className="flex items-center gap-1.5 rounded-lg border border-fasi-300 bg-white px-3 py-1.5
                               text-xs font-medium text-fasi-700 hover:bg-fasi-50 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Exportar CSV
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-fasi-500 text-white">
                      {['Docente', 'Projeto', 'Natureza', 'Edital', 'Ano', 'Solicitação', 'Status'].map(h => (
                        <th key={h} className="px-3 py-2.5 text-left font-medium whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={r.id} className={i % 2 === 0 ? 'bg-white' : 'bg-fasi-50/30'}>
                        <td className="px-3 py-2 whitespace-nowrap">{r.docente}</td>
                        <td className="px-3 py-2 max-w-[220px] truncate" title={r.nome_projeto}>{r.nome_projeto}</td>
                        <td className="px-3 py-2 whitespace-nowrap">{r.natureza}</td>
                        <td className="px-3 py-2 whitespace-nowrap">{r.edital}</td>
                        <td className="px-3 py-2 whitespace-nowrap">{r.ano_edital}</td>
                        <td className="px-3 py-2 whitespace-nowrap">{r.solicitacao}</td>
                        <td className="px-3 py-2">
                          <select
                            value={r.status ?? 'recebido'}
                            onChange={e => statusMutation.mutate({ id: r.id, status: e.target.value })}
                            disabled={statusMutation.isPending}
                            className={`rounded border px-2 py-0.5 text-xs font-medium cursor-pointer
                                        focus:outline-none focus:ring-1 focus:ring-fasi-400
                                        disabled:opacity-50 ${statusStyle(r.status ?? 'recebido')}`}
                          >
                            {STATUS_OPTIONS.map(s => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!isLoading && allRows.length === 0 && (
        <div className="fasi-info-box">Nenhum projeto encontrado no banco de dados.</div>
      )}
    </PageShell>
  )
}
