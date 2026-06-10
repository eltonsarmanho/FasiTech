import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useState, useMemo } from 'react'
import { Loader2, Play, Check, X, Trash2 } from 'lucide-react'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { apiAuth } from '@/shared/lib/api'
import { POLOS } from '@/shared/lib/constants'

type TipoFormulario = 'ACC' | 'TCC' | 'Estagio'

const COMPONENTES_ESTAGIO = [
  'Plano de Estágio (Estágio I)',
  'Relatório Final (Estágio II)',
]

function unique(rows: Record<string, string>[], key: string): string[] {
  return Array.from(new Set(rows.map(r => r[key] ?? '').filter(Boolean))).sort()
}

export function LancamentoConceitos() {
  const [tipo, setTipo] = useState<TipoFormulario>('ACC')
  const [filtroTurma, setFiltroTurma] = useState('')
  const [filtroPolo, setFiltroPolo] = useState('')
  const [filtroPeriodo, setFiltroPeriodo] = useState('')
  const [filtroMatricula, setFiltroMatricula] = useState('')
  const [filtroEstagio, setFiltroEstagio] = useState('')
  const [somentePendentes, setSomentePendentes] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['lancamentos', tipo],
    queryFn: async () => {
      const params = new URLSearchParams({ tipo_formulario: tipo })
      return (await apiAuth.get(`/api/admin/lancamentos?${params}`)).data
    },
  })

  const rows: Record<string, any>[] = Array.isArray(data) ? data : []

  const filtered = useMemo(() => {
    return rows.filter(r => {
      if (filtroTurma && r.turma !== filtroTurma) return false
      if (filtroPolo && r.polo !== filtroPolo) return false
      if (filtroPeriodo && r.periodo !== filtroPeriodo) return false
      if (filtroMatricula && r.matricula !== filtroMatricula) return false
      if (filtroEstagio && r.componente !== filtroEstagio) return false
      if (somentePendentes && r.matriculado && r.consolidado) return false
      return true
    })
  }, [rows, filtroTurma, filtroPolo, filtroPeriodo, filtroMatricula, filtroEstagio, somentePendentes])

  function resetFiltros() {
    setFiltroTurma(''); setFiltroPolo(''); setFiltroPeriodo('')
    setFiltroMatricula(''); setFiltroEstagio(''); setSomentePendentes(false)
  }

  const queryClient = useQueryClient()

  const matricularMutation = useMutation({
    mutationFn: (row: { matricula: string; periodo: string; polo: string; componente: string }) =>
      apiAuth.post('/api/admin/lancamentos/matricular', row),
    onSuccess: () => {
      toast.success('Matrícula processada! Status atualizado automaticamente.')
      // Recarregar dados após sucesso
      queryClient.invalidateQueries({ queryKey: ['lancamentos'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Erro ao matricular no SIGAA')
    },
  })

  const consolidarMutation = useMutation({
    mutationFn: (row: { matricula: string; periodo: string; polo: string; componente: string }) =>
      apiAuth.post('/api/admin/lancamentos/consolidar', row),
    onSuccess: () => {
      toast.success('Consolidação processada! Status atualizado automaticamente.')
      // Recarregar dados após sucesso
      queryClient.invalidateQueries({ queryKey: ['lancamentos'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Erro ao consolidar no SIGAA')
    },
  })

  const atualizarStatusMutation = useMutation({
    mutationFn: (data: { matricula: string; periodo: string; polo: string; componente: string; matriculado?: boolean; consolidado?: boolean }) =>
      apiAuth.patch('/api/admin/lancamentos/atualizar-status', data),
    onSuccess: () => {
      toast.success('Status atualizado com sucesso')
      // Reload data
      window.location.reload()
    },
    onError: () => toast.error('Erro ao atualizar status'),
  })

  const deletarMutation = useMutation({
    mutationFn: (row: { id: number | null; matricula: string; periodo: string; polo: string; componente: string }) =>
      apiAuth.delete('/api/admin/lancamentos', {
        data: { ...row, tipo_formulario: tipo },
      }),
    onSuccess: (_, row) => {
      toast.success(`Registro de ${row.matricula} excluído com sucesso`)
      queryClient.invalidateQueries({ queryKey: ['lancamentos', tipo] })
    },
    onError: () => toast.error('Erro ao excluir registro'),
  })

  return (
    <PageShell icon="📝" title="Lançamento de Conceitos"
      subtitle="Painel restrito automação SIGAA para ACC, TCC e Estágio">
      <div className="fasi-info-box mb-6 border-amber-200 bg-amber-50 text-amber-800">
        ⚠️ As ações de matrícula e consolidação acessam o SIGAA diretamente via automação. Use com cuidado.
      </div>

      {/* Seleção do tipo */}
      <div className="fasi-card p-4 mb-4">
        <p className="text-sm font-medium text-foreground mb-3">Tipo de lançamento</p>
        <div className="flex gap-3">
          {(['ACC', 'TCC', 'Estagio'] as TipoFormulario[]).map(t => (
            <button
              key={t}
              onClick={() => { setTipo(t); resetFiltros() }}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                tipo === t
                  ? 'bg-fasi-500 text-white'
                  : 'bg-fasi-50 text-fasi-700 hover:bg-fasi-100'
              }`}
            >
              {t === 'Estagio' ? 'Estágio' : t}
            </button>
          ))}
        </div>
      </div>

      {/* Filtros */}
      <FormSection title="Filtros">
        <FieldGroup cols={tipo === 'Estagio' ? 3 : 2}>
          <Field label="Turma">
            <select className="fasi-input" value={filtroTurma}
              onChange={e => setFiltroTurma(e.target.value)}>
              <option value="">Todas</option>
              {unique(rows, 'turma').map(v => <option key={v}>{v}</option>)}
            </select>
          </Field>
          <Field label="Polo">
            <select className="fasi-input" value={filtroPolo}
              onChange={e => setFiltroPolo(e.target.value)}>
              <option value="">Todos</option>
              {POLOS.map(p => <option key={p}>{p}</option>)}
            </select>
          </Field>
          <Field label="Período">
            <select className="fasi-input" value={filtroPeriodo}
              onChange={e => setFiltroPeriodo(e.target.value)}>
              <option value="">Todos</option>
              {unique(rows, 'periodo').map(v => <option key={v}>{v}</option>)}
            </select>
          </Field>
          <Field label="Matrícula">
            <select className="fasi-input" value={filtroMatricula}
              onChange={e => setFiltroMatricula(e.target.value)}>
              <option value="">Todas</option>
              {unique(rows, 'matricula').map(v => <option key={v}>{v}</option>)}
            </select>
          </Field>
          {tipo === 'Estagio' && (
            <Field label="Componente de Estágio">
              <select className="fasi-input" value={filtroEstagio}
                onChange={e => setFiltroEstagio(e.target.value)}>
                <option value="">Todos</option>
                {COMPONENTES_ESTAGIO.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
          )}
        </FieldGroup>
        <label className="flex items-center gap-2 mt-3 cursor-pointer">
          <input type="checkbox" checked={somentePendentes}
            onChange={e => setSomentePendentes(e.target.checked)}
            className="w-4 h-4" />
          <span className="text-sm text-foreground">
            Somente pendentes (Matriculado=Não ou Consolidado=Não)
          </span>
        </label>
      </FormSection>

      {/* Total */}
      {rows.length > 0 && (
        <div className="fasi-card p-4 mb-4 text-center">
          <p className="text-2xl font-bold text-fasi-600">{filtered.length}</p>
          <p className="text-xs text-muted-foreground">
            aluno{filtered.length !== 1 ? 's' : ''} encontrado{filtered.length !== 1 ? 's' : ''}
            {filtered.length !== rows.length && ` (de ${rows.length} total)`}
          </p>
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 animate-spin text-fasi-500" />
        </div>
      )}

      {!isLoading && rows.length === 0 && (
        <div className="fasi-info-box">Nenhum aluno encontrado para {tipo === 'Estagio' ? 'Estágio' : tipo}.</div>
      )}

      {filtered.length > 0 && (
        <div className="fasi-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-fasi-500 text-white">
                  <th className="px-3 py-2.5 text-left">Matrícula</th>
                  <th className="px-3 py-2.5 text-left">Período</th>
                  <th className="px-3 py-2.5 text-left">Turma</th>
                  <th className="px-3 py-2.5 text-left">Polo</th>
                  <th className="px-3 py-2.5 text-left">Componente</th>
                  <th className="px-3 py-2.5 text-left">Matriculado</th>
                  <th className="px-3 py-2.5 text-left">Consolidado</th>
                  <th className="px-3 py-2.5 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-fasi-50/30'}>
                    <td className="px-3 py-2">{row.matricula}</td>
                    <td className="px-3 py-2">{row.periodo}</td>
                    <td className="px-3 py-2">{row.turma}</td>
                    <td className="px-3 py-2">{row.polo}</td>
                    <td className="px-3 py-2">{row.componente}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <span className={`fasi-badge ${row.matriculado ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {row.matriculado ? 'Sim' : 'Não'}
                        </span>
                        <button
                          onClick={() => atualizarStatusMutation.mutate({
                            matricula: row.matricula,
                            periodo: row.periodo,
                            polo: row.polo,
                            componente: row.componente,
                            matriculado: !row.matriculado
                          })}
                          disabled={atualizarStatusMutation.isPending}
                          className="p-1 rounded hover:bg-gray-100 transition-colors"
                          title={`Alterar de ${row.matriculado ? 'Sim' : 'Não'} para ${row.matriculado ? 'Não' : 'Sim'}`}
                        >
                          {row.matriculado ? (
                            <Check className="w-4 h-4 text-green-600" />
                          ) : (
                            <X className="w-4 h-4 text-red-600" />
                          )}
                        </button>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <span className={`fasi-badge ${row.consolidado ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                          {row.consolidado ? 'Sim' : 'Pendente'}
                        </span>
                        <button
                          onClick={() => atualizarStatusMutation.mutate({
                            matricula: row.matricula,
                            periodo: row.periodo,
                            polo: row.polo,
                            componente: row.componente,
                            consolidado: !row.consolidado
                          })}
                          disabled={atualizarStatusMutation.isPending}
                          className="p-1 rounded hover:bg-gray-100 transition-colors"
                          title={`Alterar de ${row.consolidado ? 'Sim' : 'Não'} para ${row.consolidado ? 'Não' : 'Sim'}`}
                        >
                          {row.consolidado ? (
                            <Check className="w-4 h-4 text-green-600" />
                          ) : (
                            <X className="w-4 h-4 text-yellow-600" />
                          )}
                        </button>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1.5 justify-center flex-col items-center">
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => matricularMutation.mutate({ matricula: row.matricula, periodo: row.periodo, polo: row.polo, componente: row.componente })}
                            disabled={matricularMutation.isPending || consolidarMutation.isPending}
                            className="fasi-btn-outline py-1 px-2 text-xs"
                            title="Matricular no SIGAA"
                          >
                            {matricularMutation.isPending ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                            {matricularMutation.isPending ? 'Aguarde...' : 'Matricular'}
                          </button>
                          <button
                            onClick={() => consolidarMutation.mutate({ matricula: row.matricula, periodo: row.periodo, polo: row.polo, componente: row.componente })}
                            disabled={matricularMutation.isPending || consolidarMutation.isPending}
                            className="fasi-btn-secondary py-1 px-2 text-xs"
                            title="Consolidar no SIGAA"
                          >
                            {consolidarMutation.isPending ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                            {consolidarMutation.isPending ? 'Aguarde...' : 'Consolidar'}
                          </button>
                          <button
                            onClick={() => {
                              if (window.confirm(`Excluir registro de ${row.matricula} (${row.componente})?\n\nIsso removerá o lançamento, a submissão do formulário e a pasta no Google Drive.`)) {
                                deletarMutation.mutate({
                                  id: row.id ?? null,
                                  matricula: row.matricula,
                                  periodo: row.periodo,
                                  polo: row.polo,
                                  componente: row.componente,
                                })
                              }
                            }}
                            disabled={deletarMutation.isPending}
                            className="fasi-btn-outline py-1 px-2 text-xs text-red-600 border-red-300 hover:bg-red-50"
                            title="Excluir registro e pasta no Drive"
                          >
                            {deletarMutation.isPending
                              ? <Loader2 className="w-3 h-3 animate-spin" />
                              : <Trash2 className="w-3 h-3" />}
                          </button>
                        </div>
                        {(matricularMutation.isPending || consolidarMutation.isPending) && (
                          <p className="text-xs text-amber-600 font-medium">⏳ Processando...</p>
                        )}
                      </div>
                    </td>
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
