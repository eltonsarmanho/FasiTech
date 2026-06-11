import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Users, ShieldCheck, HeartPulse, BookOpen } from 'lucide-react'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection } from '@/shared/components/FormSection'
import { TokenGate } from '@/shared/components/TokenGate'
import { apiAuth } from '@/shared/lib/api'

// ── Tipos ─────────────────────────────────────────────────────────────────────

interface DashboardData {
  total: number
  pct_pcd: number
  pct_assistencia: number
  saude_media: number | null
  polos: string[]
  periodos: string[]
  distribuicoes: {
    genero: Record<string, number>
    cor_etnia: Record<string, number>
    renda: Record<string, number>
    moradia: Record<string, number>
    trabalho: Record<string, number>
    deslocamento: Record<string, number>
    acesso_internet: Record<string, number>
    saude_mental: Record<string, number>
    assistencia_estudantil: Record<string, number>
    escolaridade_pai: Record<string, number>
    escolaridade_mae: Record<string, number>
  }
}

// ── Ordenações canônicas para exibição ────────────────────────────────────────

const ORDER_RENDA = [
  'Até 1 salário mínimo',
  '1 a 3 salários mínimos',
  '3 a 5 salários mínimos',
  'Acima de 5 salários mínimos',
  'Acima de 5 a 10 salários mínimos',
]

const ORDER_SAUDE = ['Muito boa', 'Boa', 'Regular', 'Ruim', 'Muito ruim', 'Prefiro não responder']

const ORDER_ESCOLARIDADE = [
  'Analfabeto',
  'Sem escolaridade',
  'Ensino Fundamental incompleto',
  'Ensino Fundamental completo',
  'Ensino Médio incompleto',
  'Ensino Médio completo',
  'Ensino Superior incompleto',
  'Ensino Superior completo',
  'Pós-graduação',
  'Não sei/Prefiro não responder',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function saudeColor(score: number | null): string {
  if (score === null) return 'text-gray-400'
  if (score >= 4.5) return 'text-green-600'
  if (score >= 3.5) return 'text-lime-600'
  if (score >= 2.5) return 'text-amber-600'
  if (score >= 1.5) return 'text-orange-600'
  return 'text-red-600'
}

function saudeLabel(score: number | null): string {
  if (score === null) return '—'
  if (score >= 4.5) return 'Muito boa'
  if (score >= 3.5) return 'Boa'
  if (score >= 2.5) return 'Regular'
  if (score >= 1.5) return 'Ruim'
  return 'Muito ruim'
}

function sortedEntries(
  dist: Record<string, number>,
  order?: string[],
): [string, number][] {
  if (order) {
    const ordered = order
      .filter(k => dist[k] !== undefined)
      .map(k => [k, dist[k]] as [string, number])
    const rest = Object.entries(dist)
      .filter(([k]) => !order.includes(k))
      .sort((a, b) => b[1] - a[1])
    return [...ordered, ...rest]
  }
  return Object.entries(dist).sort((a, b) => b[1] - a[1])
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function KpiCard({
  icon: Icon,
  label,
  value,
  sub,
  valueColor = 'text-fasi-500',
}: {
  icon: React.ElementType
  label: string
  value: string
  sub?: string
  valueColor?: string
}) {
  return (
    <div className="fasi-card p-5 flex items-start gap-4">
      <div className="shrink-0 mt-0.5 text-fasi-500">
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground mb-1">{label}</p>
        <p className={`text-2xl font-bold leading-none ${valueColor}`}>{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </div>
    </div>
  )
}

const SENTIMENT_COLORS = [
  'bg-green-500',
  'bg-lime-500',
  'bg-amber-400',
  'bg-orange-500',
  'bg-red-500',
  'bg-gray-400',
]

function DistBar({
  label,
  count,
  total,
  maxCount,
  color = 'bg-fasi-500',
}: {
  label: string
  count: number
  total: number
  maxCount: number
  color?: string
}) {
  const pct = maxCount > 0 ? (count / maxCount) * 100 : 0
  const pctOfTotal = total > 0 ? ((count / total) * 100).toFixed(1) : '0'
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-muted-foreground w-48 shrink-0 text-right leading-tight">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
        <div
          className={`h-5 rounded-full ${color} flex items-center justify-end pr-2 transition-all duration-500`}
          style={{ width: `${Math.max(pct, 0)}%` }}
        >
          {pct >= 8 && (
            <span className="text-white text-[11px] font-semibold">{count}</span>
          )}
        </div>
      </div>
      <span className="text-xs text-muted-foreground w-14 shrink-0">{pctOfTotal}%</span>
    </div>
  )
}

function DistSection({
  title,
  dist,
  order,
  sentiment = false,
}: {
  title: string
  dist: Record<string, number>
  order?: string[]
  sentiment?: boolean
}) {
  const entries = sortedEntries(dist, order)
  const total = entries.reduce((s, [, v]) => s + v, 0)
  const maxCount = Math.max(...entries.map(([, v]) => v), 1)

  if (entries.length === 0) {
    return (
      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">{title}</p>
        <p className="text-xs text-muted-foreground">Sem dados</p>
      </div>
    )
  }

  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">{title}</p>
      <div className="space-y-2">
        {entries.map(([label, count], i) => (
          <DistBar
            key={label}
            label={label}
            count={count}
            total={total}
            maxCount={maxCount}
            color={sentiment ? SENTIMENT_COLORS[i % SENTIMENT_COLORS.length] : 'bg-fasi-500'}
          />
        ))}
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────

export function ConsultaSocial() {
  const [filtroPolo, setFiltroPolo] = useState('')
  const [filtroPeriodo, setFiltroPeriodo] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['social-dashboard', filtroPolo, filtroPeriodo],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filtroPolo) params.set('polo', filtroPolo)
      if (filtroPeriodo) params.set('periodo', filtroPeriodo)
      const qs = params.toString()
      return (
        await apiAuth.get<DashboardData>(
          `/api/v1/dados-sociais/dashboard${qs ? `?${qs}` : ''}`,
        )
      ).data
    },
  })

  const total = data?.total ?? 0
  const polos = data?.polos ?? []
  const periodos = data?.periodos ?? []
  const d = data?.distribuicoes

  return (
    <PageShell
      icon="📊"
      title="Dashboard Social"
      subtitle="Perfil socioeconômico dos discentes da FASI/UFPA"
    >
      <TokenGate storageKey="fasi_config_auth">

        {/* ── Filtros ── */}
        <div className="fasi-card p-4 mb-6 flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-foreground">Filtros:</span>

          <select
            className="fasi-input w-auto min-w-[160px]"
            value={filtroPolo}
            onChange={e => setFiltroPolo(e.target.value)}
          >
            <option value="">Todos os polos</option>
            {polos.map(p => <option key={p} value={p}>{p}</option>)}
          </select>

          <select
            className="fasi-input w-auto min-w-[160px]"
            value={filtroPeriodo}
            onChange={e => setFiltroPeriodo(e.target.value)}
          >
            <option value="">Todos os períodos</option>
            {periodos.map(p => <option key={p} value={p}>{p}</option>)}
          </select>

          {(filtroPolo || filtroPeriodo) && (
            <button
              className="fasi-btn-outline py-1 px-3 text-sm"
              onClick={() => { setFiltroPolo(''); setFiltroPeriodo('') }}
            >
              Limpar
            </button>
          )}
        </div>

        {/* ── Loading ── */}
        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="w-7 h-7 animate-spin text-fasi-500" />
          </div>
        )}

        {!isLoading && total === 0 && (
          <div className="fasi-info-box">
            Nenhuma resposta encontrada{filtroPolo || filtroPeriodo ? ' para os filtros selecionados' : ''}.
          </div>
        )}

        {!isLoading && total > 0 && d && (
          <div className="space-y-6">

            {/* ── KPI Cards ── */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <KpiCard
                icon={Users}
                label="Total de respostas"
                value={String(total)}
                sub={[filtroPolo, filtroPeriodo].filter(Boolean).join(' · ') || 'Todos os filtros'}
              />
              <KpiCard
                icon={ShieldCheck}
                label="Alunos PCD"
                value={`${data.pct_pcd}%`}
                sub="Pessoas com deficiência"
                valueColor={data.pct_pcd > 0 ? 'text-fasi-500' : 'text-gray-400'}
              />
              <KpiCard
                icon={BookOpen}
                label="Recebem assistência"
                value={`${data.pct_assistencia}%`}
                sub="Assistência estudantil"
                valueColor={data.pct_assistencia > 0 ? 'text-green-600' : 'text-gray-400'}
              />
              <KpiCard
                icon={HeartPulse}
                label="Saúde mental média"
                value={data.saude_media !== null ? `${data.saude_media} / 5` : '—'}
                sub={saudeLabel(data.saude_media)}
                valueColor={saudeColor(data.saude_media)}
              />
            </div>

            {/* ── Identidade & Diversidade ── */}
            <FormSection title="👤 Identidade & Diversidade">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <DistSection title="Gênero" dist={d.genero} />
                <DistSection title="Cor / Etnia" dist={d.cor_etnia} />
              </div>
            </FormSection>

            {/* ── Situação Socioeconômica ── */}
            <FormSection title="💰 Situação Socioeconômica">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <DistSection title="Renda Familiar" dist={d.renda} order={ORDER_RENDA} />
                <DistSection title="Tipo de Moradia" dist={d.moradia} />
              </div>
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-8">
                <DistSection title="Situação de Trabalho" dist={d.trabalho} />
                <DistSection title="Meio de Deslocamento" dist={d.deslocamento} />
              </div>
            </FormSection>

            {/* ── Saúde & Bem-estar ── */}
            <FormSection title="❤️ Saúde & Bem-estar">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <DistSection
                  title="Saúde Mental"
                  dist={d.saude_mental}
                  order={ORDER_SAUDE}
                  sentiment
                />
                <DistSection
                  title="Assistência Estudantil"
                  dist={d.assistencia_estudantil}
                />
              </div>
            </FormSection>

            {/* ── Tecnologia ── */}
            <FormSection title="🌐 Acesso à Tecnologia">
              <div className="max-w-md">
                <DistSection
                  title="Qualidade do Acesso à Internet"
                  dist={d.acesso_internet}
                />
              </div>
            </FormSection>

            {/* ── Escolaridade dos pais ── */}
            <FormSection title="🎓 Escolaridade dos Pais">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <DistSection
                  title="Escolaridade do Pai"
                  dist={d.escolaridade_pai}
                  order={ORDER_ESCOLARIDADE}
                />
                <DistSection
                  title="Escolaridade da Mãe"
                  dist={d.escolaridade_mae}
                  order={ORDER_ESCOLARIDADE}
                />
              </div>
            </FormSection>

          </div>
        )}
      </TokenGate>
    </PageShell>
  )
}
