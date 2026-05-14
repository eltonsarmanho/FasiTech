import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, RefreshCw, ExternalLink } from 'lucide-react'
import { PageShell } from '@/shared/components/PageShell'
import { api } from '@/shared/lib/api'
import { cn } from '@/shared/lib/utils'

type CellValue = { text: string; url: string | null }
type TabData = { aba: string; colunas: string[]; dados: Record<string, CellValue>[] }
type OfertasResponse = { abas_oferta: TabData[]; abas_grade: TabData[]; mensagem?: string }

function DataTable({ tab }: { tab: TabData }) {
  return (
    <div className="fasi-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-fasi-500 text-white">
              {tab.colunas.map(col => (
                <th key={col} className="px-4 py-3 text-left font-semibold whitespace-nowrap">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tab.dados.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-fasi-50/40'}>
                {tab.colunas.map(col => {
                  const cell = row[col] ?? { text: '—', url: null }
                  return (
                    <td key={col} className="px-4 py-2.5 text-foreground whitespace-nowrap">
                      {cell.url ? (
                        <a href={cell.url} target="_blank" rel="noopener noreferrer"
                          className="text-fasi-600 hover:text-fasi-700 underline inline-flex items-center gap-1">
                          {cell.text || 'Abrir'} <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (cell.text || '—')}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TabGroup({ tabs }: { tabs: TabData[] }) {
  const [active, setActive] = useState(0)
  if (tabs.length === 0) {
    return <div className="fasi-info-box">Nenhuma aba disponível para esta seção.</div>
  }
  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {tabs.map((t, i) => (
          <button key={t.aba} onClick={() => setActive(i)}
            className={cn('px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              active === i ? 'bg-fasi-500 text-white' : 'bg-muted text-foreground hover:bg-fasi-100')}>
            {t.aba}
          </button>
        ))}
      </div>
      {tabs[active] && <DataTable tab={tabs[active]} />}
    </div>
  )
}

export function OfertasDisciplinas() {
  const [section, setSection] = useState<'oferta' | 'grade'>('oferta')

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['ofertas-disciplinas'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/ofertas-disciplinas')
      return data as OfertasResponse
    },
  })

  const hasOferta = (data?.abas_oferta?.length ?? 0) > 0
  const hasGrade = (data?.abas_grade?.length ?? 0) > 0

  return (
    <PageShell icon="📅" title="Ofertas de Disciplinas"
      subtitle="Disciplinas ofertadas por período — dados da planilha institucional">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex gap-2">
          {(hasOferta || (!isLoading && !hasGrade)) && (
            <button onClick={() => setSection('oferta')}
              className={cn('px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                section === 'oferta' ? 'bg-fasi-500 text-white' : 'fasi-btn-outline')}>
              📊 Ofertas
            </button>
          )}
          {hasGrade && (
            <button onClick={() => setSection('grade')}
              className={cn('px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                section === 'grade' ? 'bg-fasi-500 text-white' : 'fasi-btn-outline')}>
              📋 Grades
            </button>
          )}
        </div>
        <button onClick={() => refetch()} className="fasi-btn-outline py-1.5 text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Atualizar
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-48 text-muted-foreground gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-fasi-500" />
          Carregando ofertas...
        </div>
      )}

      {error && (
        <div className="fasi-info-box border-red-200 bg-red-50 text-red-700">
          Não foi possível carregar as ofertas. Verifique a planilha de configuração.
        </div>
      )}

      {data?.mensagem && !hasOferta && !hasGrade && (
        <div className="fasi-info-box">{data.mensagem}</div>
      )}

      {data && (
        <>
          {section === 'oferta' && <TabGroup tabs={data.abas_oferta ?? []} />}
          {section === 'grade' && <TabGroup tabs={data.abas_grade ?? []} />}
        </>
      )}
    </PageShell>
  )
}
