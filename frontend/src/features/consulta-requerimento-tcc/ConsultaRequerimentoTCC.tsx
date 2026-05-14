import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { apiAuth } from '@/shared/lib/api'
import { formatDate } from '@/shared/lib/utils'

type Row = Record<string, string>

function unique(rows: Row[], key: string): string[] {
  return Array.from(new Set(rows.map(r => r[key] ?? '').filter(Boolean))).sort()
}

export function ConsultaRequerimentoTCC() {
  const [filtroOrientador, setFiltroOrientador] = useState('')
  const [filtroModalidade, setFiltroModalidade] = useState('')
  const [filtroDataDe, setFiltroDataDe] = useState('')
  const [filtroDataAte, setFiltroDataAte] = useState('')

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

  return (
    <PageShell icon="📋" title="Consulta — Requerimento TCC"
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
          <div className="p-4 border-b border-border">
            <span className="text-sm font-semibold text-foreground">
              {filtered.length} registro{filtered.length !== 1 ? 's' : ''}
              {hasFilters && rows.length !== filtered.length && ` (de ${rows.length} total)`}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-fasi-500 text-white">
                  {['Aluno', 'Matrícula', 'Orientador', 'Título', 'Modalidade', 'Defesa'].map(h => (
                    <th key={h} className="px-3 py-2.5 text-left font-medium whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-fasi-50/30'}>
                    <td className="px-3 py-2 whitespace-nowrap">{r.nome_aluno}</td>
                    <td className="px-3 py-2">{r.matricula}</td>
                    <td className="px-3 py-2 whitespace-nowrap">{r.orientador}</td>
                    <td className="px-3 py-2 max-w-[200px] truncate" title={r.titulo_trabalho}>{r.titulo_trabalho}</td>
                    <td className="px-3 py-2">{r.modalidade}</td>
                    <td className="px-3 py-2 whitespace-nowrap">{r.data_defesa ? formatDate(r.data_defesa) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PageShell>
  )
}
