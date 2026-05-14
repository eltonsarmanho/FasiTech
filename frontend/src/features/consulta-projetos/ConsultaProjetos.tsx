import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { PageShell } from '@/shared/components/PageShell'
import { apiAuth } from '@/shared/lib/api'
import { formatDate } from '@/shared/lib/utils'

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
  const [filterDocente, setFilterDocente] = useState('Todos')
  const [filterNatureza, setFilterNatureza] = useState('Todas')
  const [filterAno, setFilterAno] = useState('Todos')

  const { data, isLoading } = useQuery({
    queryKey: ['projetos-list'],
    queryFn: async () => (await apiAuth.get('/api/v1/projetos?por_pagina=1000')).data,
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
      return true
    })
  }, [allRows, filterDocente, filterNatureza, filterAno])

  const countNatureza = (term: string) =>
    rows.filter(r => r.natureza?.toLowerCase().includes(term)).length

  const hasFilters = filterDocente !== 'Todos' || filterNatureza !== 'Todas' || filterAno !== 'Todos'

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
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FilterSelect label="Docente" value={filterDocente} onChange={setFilterDocente} options={docentes} />
              <FilterSelect label="Natureza" value={filterNatureza} onChange={setFilterNatureza} options={naturezas} />
              <FilterSelect label="Ano do Edital" value={filterAno} onChange={setFilterAno} options={anos} />
            </div>
            {hasFilters && (
              <button
                onClick={() => { setFilterDocente('Todos'); setFilterNatureza('Todas'); setFilterAno('Todos') }}
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
                <span className="text-sm font-semibold text-foreground">{rows.length} projeto{rows.length !== 1 ? 's' : ''}</span>
                {hasFilters && (
                  <span className="text-xs text-muted-foreground">de {allRows.length} no total</span>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-fasi-500 text-white">
                      {['Docente', 'Projeto', 'Natureza', 'Edital', 'Ano', 'Solicitação', 'Enviado em', 'Status'].map(h => (
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
                        <td className="px-3 py-2 whitespace-nowrap">{r.submission_date ? formatDate(r.submission_date) : '—'}</td>
                        <td className="px-3 py-2">
                          <span className="fasi-badge bg-fasi-50 text-fasi-700">{r.status ?? 'recebido'}</span>
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
