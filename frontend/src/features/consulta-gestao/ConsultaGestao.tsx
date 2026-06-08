import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, BarChart2, Star, Users, TrendingUp } from 'lucide-react'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection } from '@/shared/components/FormSection'
import { TokenGate } from '@/shared/components/TokenGate'
import { apiAuth } from '@/shared/lib/api'

// ── Tipos ────────────────────────────────────────────────────────────────────

interface SubmissionItem {
  id: number
  periodo: string | null
  q1_valor: number | null
  q2_valor: number | null
  q3_valor: number | null
  q4_valor: number | null
  q5_valor: number | null
  q6_valor: number | null
  q7_valor: number | null
  q8_valor: number | null
  q9_valor: number | null
  q12_valor: number | null
  q13_fasitech_funcionalidades: string[]
  submission_date: string | null
}

// ── Metadados das perguntas ───────────────────────────────────────────────────

const DIMENSOES = [
  { key: 'q1_valor', label: 'Transparência', descricao: 'Transparência da gestão' },
  { key: 'q2_valor', label: 'Comunicação', descricao: 'Comunicação com alunos e professores' },
  { key: 'q3_valor', label: 'Acessibilidade', descricao: 'Acessibilidade para questões/preocupações' },
  { key: 'q4_valor', label: 'Inclusão', descricao: 'Ambiente acadêmico inclusivo e diversificado' },
  { key: 'q5_valor', label: 'Planejamento', descricao: 'Planejamento de atividades acadêmicas' },
  { key: 'q6_valor', label: 'Recursos', descricao: 'Gestão de recursos (infra, tecnologia, materiais)' },
  { key: 'q7_valor', label: 'Eficiência', descricao: 'Eficiência em resolver problemas administrativos' },
  { key: 'q8_valor', label: 'Suporte', descricao: 'Suporte acadêmico e orientação ao aluno' },
  { key: 'q9_valor', label: 'Extracurricular', descricao: 'Promoção de atividades extracurriculares' },
] as const

const OPCOES_SCALE = ['Muito insatisfeito / Discordo totalmente', 'Insatisfeito / Discordo', 'Neutro', 'Satisfeito / Concordo', 'Muito satisfeito / Concordo totalmente']

const OPCOES_IMPACTO = ['Discordo totalmente', 'Discordo', 'Neutro', 'Concordo', 'Concordo totalmente']

const FASITECH_FEATURES = [
  'Formulário de ACC',
  'Formulário de TCC',
  'Formulário de Estágio',
  'Requerimento de TCC',
  'Emissão de Documentos',
  'Formulário Social',
  'FAQ / Assistente IA (Diretor Virtual)',
  'Nenhuma',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function avg(values: (number | null)[]): number | null {
  const valid = values.filter((v): v is number => v !== null && v !== undefined)
  if (valid.length === 0) return null
  return valid.reduce((a, b) => a + b, 0) / valid.length
}

function scoreColor(score: number | null): string {
  if (score === null) return 'bg-gray-300'
  if (score >= 4.2) return 'bg-green-500'
  if (score >= 3.5) return 'bg-lime-500'
  if (score >= 2.8) return 'bg-amber-400'
  if (score >= 2) return 'bg-orange-500'
  return 'bg-red-500'
}

function scoreBadgeColor(score: number | null): string {
  if (score === null) return 'text-gray-400'
  if (score >= 4.2) return 'text-green-600'
  if (score >= 3.5) return 'text-lime-600'
  if (score >= 2.8) return 'text-amber-600'
  if (score >= 2) return 'text-orange-600'
  return 'text-red-600'
}

function scoreBgBadge(score: number | null): string {
  if (score === null) return 'bg-gray-100 text-gray-500'
  if (score >= 4.2) return 'bg-green-100 text-green-700'
  if (score >= 3.5) return 'bg-lime-100 text-lime-700'
  if (score >= 2.8) return 'bg-amber-100 text-amber-700'
  if (score >= 2) return 'bg-orange-100 text-orange-700'
  return 'bg-red-100 text-red-700'
}

function countByValue(items: SubmissionItem[], key: keyof SubmissionItem): Record<number, number> {
  const counts: Record<number, number> = {}
  for (let i = 1; i <= 5; i++) counts[i] = 0
  for (const item of items) {
    const v = item[key] as number | null
    if (v !== null && v !== undefined && v >= 1 && v <= 5) {
      counts[v] = (counts[v] || 0) + 1
    }
  }
  return counts
}

const DIST_COLORS = [
  'bg-red-500',
  'bg-orange-400',
  'bg-amber-400',
  'bg-lime-500',
  'bg-green-500',
]

// ── Sub-componentes ───────────────────────────────────────────────────────────

function KpiCard({
  icon: Icon,
  label,
  value,
  sub,
  color = 'text-fasi-500',
}: {
  icon: React.ElementType
  label: string
  value: string
  sub?: string
  color?: string
}) {
  return (
    <div className="fasi-card p-5 flex items-start gap-4">
      <div className={`shrink-0 mt-0.5 ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground mb-1">{label}</p>
        <p className="text-2xl font-bold text-foreground leading-none">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </div>
    </div>
  )
}

function DimensaoBar({ label, descricao, score, counts, total }: {
  label: string
  descricao: string
  score: number | null
  counts: Record<number, number>
  total: number
}) {
  const pct = score !== null ? ((score - 1) / 4) * 100 : 0

  return (
    <div className="py-3 border-b border-border last:border-0">
      <div className="flex items-center justify-between mb-1.5 gap-3">
        <div>
          <span className="font-semibold text-sm text-foreground">{label}</span>
          <span className="text-xs text-muted-foreground ml-2">{descricao}</span>
        </div>
        <span className={`text-sm font-bold px-2 py-0.5 rounded-full shrink-0 ${scoreBgBadge(score)}`}>
          {score !== null ? score.toFixed(2) : '—'} / 5
        </span>
      </div>

      {/* Barra de média */}
      <div className="w-full bg-gray-100 rounded-full h-3 mb-2 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${scoreColor(score)}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Distribuição de respostas */}
      {total > 0 && (
        <div className="flex gap-0.5 h-5 rounded overflow-hidden">
          {[1, 2, 3, 4, 5].map((v, i) => {
            const c = counts[v] ?? 0
            const p = total > 0 ? (c / total) * 100 : 0
            return p > 0 ? (
              <div
                key={v}
                className={`${DIST_COLORS[i]} flex items-center justify-center`}
                style={{ width: `${p}%` }}
                title={`${OPCOES_SCALE[i]}: ${c} (${p.toFixed(0)}%)`}
              >
                {p >= 10 && (
                  <span className="text-white text-[10px] font-semibold">{p.toFixed(0)}%</span>
                )}
              </div>
            ) : null
          })}
        </div>
      )}

      {/* Legenda distribuição compacta */}
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5">
        {[1, 2, 3, 4, 5].map((v, i) => {
          const c = counts[v] ?? 0
          if (c === 0) return null
          return (
            <span key={v} className="text-[11px] text-muted-foreground flex items-center gap-1">
              <span className={`inline-block w-2 h-2 rounded-sm ${DIST_COLORS[i]}`} />
              {c}
            </span>
          )
        })}
      </div>
    </div>
  )
}

function ImpactoBar({ counts, total }: { counts: Record<number, number>; total: number }) {
  return (
    <div className="space-y-2">
      {OPCOES_IMPACTO.map((label, i) => {
        const valor = i + 1
        const count = counts[valor] ?? 0
        const pct = total > 0 ? (count / total) * 100 : 0
        return (
          <div key={label} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-40 shrink-0 text-right">{label}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
              <div
                className={`h-5 rounded-full ${DIST_COLORS[i]} flex items-center justify-end pr-2 transition-all duration-500`}
                style={{ width: `${Math.max(pct, 0)}%` }}
              >
                {pct >= 8 && (
                  <span className="text-white text-[11px] font-semibold">{pct.toFixed(0)}%</span>
                )}
              </div>
            </div>
            <span className="text-xs text-muted-foreground w-12 shrink-0">{count} resp.</span>
          </div>
        )
      })}
    </div>
  )
}

function FuncionalidadesBar({ data, total }: { data: Record<string, number>; total: number }) {
  const sorted = FASITECH_FEATURES.filter(f => f !== 'Nenhuma')
    .map(f => ({ label: f, count: data[f] ?? 0 }))
    .sort((a, b) => b.count - a.count)

  const maxCount = Math.max(...sorted.map(s => s.count), 1)

  return (
    <div className="space-y-2">
      {sorted.map(({ label, count }) => {
        const pct = (count / maxCount) * 100
        return (
          <div key={label} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-52 shrink-0 text-right">{label}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
              <div
                className="h-5 rounded-full bg-fasi-500 flex items-center justify-end pr-2 transition-all duration-500"
                style={{ width: `${Math.max(pct, 0)}%` }}
              >
                {pct >= 8 && (
                  <span className="text-white text-[11px] font-semibold">{count}</span>
                )}
              </div>
            </div>
            <span className="text-xs text-muted-foreground w-12 shrink-0">
              {total > 0 ? `${((count / total) * 100).toFixed(0)}%` : '—'}
            </span>
          </div>
        )
      })}

      {/* Nenhuma */}
      <div className="flex items-center gap-3 pt-1 mt-1 border-t border-border">
        <span className="text-xs text-muted-foreground w-52 shrink-0 text-right">Nenhuma</span>
        <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
          <div
            className="h-5 rounded-full bg-gray-400 flex items-center justify-end pr-2 transition-all duration-500"
            style={{ width: `${total > 0 ? ((data['Nenhuma'] ?? 0) / maxCount) * 100 : 0}%` }}
          >
            {total > 0 && (data['Nenhuma'] ?? 0) / maxCount >= 0.08 && (
              <span className="text-white text-[11px] font-semibold">{data['Nenhuma'] ?? 0}</span>
            )}
          </div>
        </div>
        <span className="text-xs text-muted-foreground w-12 shrink-0">
          {total > 0 ? `${(((data['Nenhuma'] ?? 0) / total) * 100).toFixed(0)}%` : '—'}
        </span>
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────

export function ConsultaGestao() {
  const [filtroPeriodo, setFiltroPeriodo] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['avaliacao-gestao-list'],
    queryFn: async () =>
      (await apiAuth.get<{ items: SubmissionItem[]; total: number }>('/api/v1/avaliacao-gestao?por_pagina=2000')).data,
  })

  const allItems: SubmissionItem[] = data?.items ?? []

  // Períodos disponíveis
  const periodos = useMemo(
    () => Array.from(new Set(allItems.map(r => r.periodo ?? '').filter(Boolean))).sort().reverse(),
    [allItems],
  )

  const items = useMemo(
    () => (filtroPeriodo ? allItems.filter(r => r.periodo === filtroPeriodo) : allItems),
    [allItems, filtroPeriodo],
  )

  // ── Métricas gerais ──
  const total = items.length

  const mediasGerais = DIMENSOES.map(d => avg(items.map(r => r[d.key as keyof SubmissionItem] as number | null)))
  const mediaGeralGlobal = avg(mediasGerais.filter((v): v is number => v !== null))

  const melhorDimensao = DIMENSOES.reduce<{ label: string; score: number } | null>((best, d, i) => {
    const s = mediasGerais[i]
    if (s === null) return best
    if (!best || s > best.score) return { label: d.label, score: s }
    return best
  }, null)

  const impactoPositivo = items.filter(r => (r.q12_valor ?? 0) >= 4).length
  const impactoPct = total > 0 ? Math.round((impactoPositivo / total) * 100) : 0

  // ── Distribuição Q12 ──
  const q12Counts = countByValue(items, 'q12_valor')

  // ── Distribuição de funcionalidades Q13 ──
  const funcCount: Record<string, number> = {}
  for (const item of items) {
    for (const f of item.q13_fasitech_funcionalidades ?? []) {
      funcCount[f] = (funcCount[f] ?? 0) + 1
    }
  }

  return (
    <PageShell
      icon="📊"
      title="Dashboard — Avaliação da Gestão"
      subtitle="Insights quantitativos da pesquisa de avaliação da gestão FASI"
    >
      <TokenGate storageKey="fasi_config_auth">
        {/* Filtro de período */}
        <div className="fasi-card p-4 mb-6 flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-foreground">Período letivo:</span>
          <select
            className="fasi-input w-auto min-w-[160px]"
            value={filtroPeriodo}
            onChange={e => setFiltroPeriodo(e.target.value)}
          >
            <option value="">Todos os períodos</option>
            {periodos.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          {filtroPeriodo && (
            <button
              className="fasi-btn-outline py-1 px-3 text-sm"
              onClick={() => setFiltroPeriodo('')}
            >
              Limpar
            </button>
          )}
        </div>

        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="w-7 h-7 animate-spin text-fasi-500" />
          </div>
        )}

        {!isLoading && total === 0 && (
          <div className="fasi-info-box">Nenhuma avaliação encontrada{filtroPeriodo ? ` para o período ${filtroPeriodo}` : ''}.</div>
        )}

        {!isLoading && total > 0 && (
          <div className="space-y-6">

            {/* ── KPI Cards ── */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <KpiCard
                icon={Users}
                label="Total de respostas"
                value={String(total)}
                sub={filtroPeriodo ? `Período ${filtroPeriodo}` : 'Todos os períodos'}
                color="text-fasi-500"
              />
              <KpiCard
                icon={Star}
                label="Média geral (gestão)"
                value={mediaGeralGlobal !== null ? `${mediaGeralGlobal.toFixed(2)} / 5` : '—'}
                sub="Média das 9 dimensões"
                color={scoreBadgeColor(mediaGeralGlobal)}
              />
              <KpiCard
                icon={TrendingUp}
                label="Dimensão mais bem avaliada"
                value={melhorDimensao?.label ?? '—'}
                sub={melhorDimensao ? `Média ${melhorDimensao.score.toFixed(2)}` : undefined}
                color="text-green-600"
              />
              <KpiCard
                icon={BarChart2}
                label="FasiTech: impacto positivo"
                value={`${impactoPct}%`}
                sub={`${impactoPositivo} de ${total} respostas`}
                color="text-fasi-500"
              />
            </div>

            {/* ── Avaliação por Dimensão ── */}
            <FormSection title="📋 Avaliação por Dimensão (Q1–Q9)">
              <div className="mb-3 flex flex-wrap gap-3 text-xs text-muted-foreground">
                {DIST_COLORS.map((c, i) => (
                  <span key={i} className="flex items-center gap-1.5">
                    <span className={`inline-block w-3 h-3 rounded-sm ${c}`} />
                    {['Muito insatisfeito / Discordo totalmente', 'Insatisfeito / Discordo', 'Neutro', 'Satisfeito / Concordo', 'Muito satisfeito / Concordo totalmente'][i]}
                  </span>
                ))}
              </div>

              {DIMENSOES.map((d, i) => (
                <DimensaoBar
                  key={d.key}
                  label={d.label}
                  descricao={d.descricao}
                  score={mediasGerais[i]}
                  counts={countByValue(items, d.key as keyof SubmissionItem)}
                  total={items.filter(r => (r[d.key as keyof SubmissionItem] as number | null) !== null).length}
                />
              ))}

              {/* Ranking rápido */}
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">Ranking das Dimensões</p>
                <div className="space-y-1.5">
                  {DIMENSOES
                    .map((d, i) => ({ label: d.label, score: mediasGerais[i] }))
                    .filter(d => d.score !== null)
                    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
                    .map(({ label, score }, rank) => (
                      <div key={label} className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground w-5 text-right font-semibold">{rank + 1}.</span>
                        <span className="text-sm text-foreground flex-1">{label}</span>
                        <span className={`text-sm font-bold px-2 py-0.5 rounded-full ${scoreBgBadge(score)}`}>
                          {score?.toFixed(2)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </FormSection>

            {/* ── FasiTech: Impacto ── */}
            <FormSection title="🖥️ FasiTech — Impacto Percebido (Q12)">
              <p className="text-xs text-muted-foreground mb-4">
                "O FasiTech facilitou o envio e acompanhamento dos seus processos acadêmicos?"
              </p>
              <ImpactoBar
                counts={q12Counts}
                total={items.filter(r => r.q12_valor !== null).length}
              />
              <div className="mt-4 pt-4 border-t border-border grid grid-cols-2 sm:grid-cols-3 gap-3">
                {(() => {
                  const validQ12 = items.filter(r => r.q12_valor !== null)
                  const positivo = validQ12.filter(r => (r.q12_valor ?? 0) >= 4).length
                  const neutro = validQ12.filter(r => r.q12_valor === 3).length
                  const negativo = validQ12.filter(r => (r.q12_valor ?? 0) <= 2).length
                  const n = validQ12.length
                  return (
                    <>
                      <div className="fasi-card p-3 text-center">
                        <p className="text-xl font-bold text-green-600">{n > 0 ? `${Math.round((positivo / n) * 100)}%` : '—'}</p>
                        <p className="text-xs text-muted-foreground">Impacto positivo</p>
                      </div>
                      <div className="fasi-card p-3 text-center">
                        <p className="text-xl font-bold text-amber-500">{n > 0 ? `${Math.round((neutro / n) * 100)}%` : '—'}</p>
                        <p className="text-xs text-muted-foreground">Neutro</p>
                      </div>
                      <div className="fasi-card p-3 text-center">
                        <p className="text-xl font-bold text-red-500">{n > 0 ? `${Math.round((negativo / n) * 100)}%` : '—'}</p>
                        <p className="text-xs text-muted-foreground">Impacto negativo</p>
                      </div>
                    </>
                  )
                })()}
              </div>
            </FormSection>

            {/* ── FasiTech: Funcionalidades ── */}
            <FormSection title="🔧 FasiTech — Funcionalidades Utilizadas (Q13)">
              <p className="text-xs text-muted-foreground mb-4">
                Número de usuários que marcaram cada funcionalidade (múltipla escolha).
              </p>
              <FuncionalidadesBar data={funcCount} total={total} />
            </FormSection>

          </div>
        )}
      </TokenGate>
    </PageShell>
  )
}
