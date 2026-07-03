import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Trash2, Loader2, Calendar, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { TokenGate } from '@/shared/components/TokenGate'
import { apiAuth } from '@/shared/lib/api'

type TipoForm = 'tcc' | 'acc' | 'estagio' | 'ccf'

const TIPO_LABELS: Record<TipoForm, string> = {
  tcc: 'Requerimento TCC',
  acc: 'ACC',
  estagio: 'Estágio',
  ccf: 'CCF',
}

interface Periodo {
  id: number
  tipo: string
  numero: number
  data_inicio: string
  data_fim: string
  semestre: string | null
}

interface PeriodoFormData {
  numero: number
  data_inicio: string
  data_fim: string
  semestre: string
}

function formatDateBR(iso: string) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function getPeriodoStatus(p: Periodo) {
  const today = new Date().toISOString().slice(0, 10)
  if (today < p.data_inicio) return { label: 'Futuro', cls: 'bg-yellow-100 text-yellow-700' }
  if (today > p.data_fim) return { label: 'Encerrado', cls: 'bg-muted text-muted-foreground' }
  return { label: 'Aberto', cls: 'bg-green-100 text-green-700' }
}

function PeriodoForm({
  tipo,
  editing,
  onSave,
  onCancel,
  loading,
}: {
  tipo: TipoForm
  editing?: Periodo
  onSave: (data: PeriodoFormData & { tipo: TipoForm }) => void
  onCancel: () => void
  loading: boolean
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<PeriodoFormData>({
    defaultValues: editing
      ? {
          numero: editing.numero,
          data_inicio: editing.data_inicio,
          data_fim: editing.data_fim,
          semestre: editing.semestre ?? '',
        }
      : { numero: 1, data_inicio: '', data_fim: '', semestre: '' },
  })

  return (
    <form onSubmit={handleSubmit(d => onSave({ ...d, tipo }))} className="border rounded-lg p-4 bg-muted/30 mt-4">
      <p className="font-semibold text-sm mb-3">{editing ? 'Editar período' : 'Novo período'} — {TIPO_LABELS[tipo]}</p>
      <FieldGroup cols={3}>
        <Field label="Data início" required error={errors.data_inicio?.message}>
          <input className="fasi-input" type="date" {...register('data_inicio', { required: 'Obrigatório' })} />
        </Field>
        <Field label="Data fim" required error={errors.data_fim?.message}>
          <input className="fasi-input" type="date" {...register('data_fim', { required: 'Obrigatório' })} />
        </Field>
        <Field label="Semestre (opcional)">
          <input className="fasi-input" placeholder="Ex.: 2026.1" {...register('semestre')} />
        </Field>
      </FieldGroup>
      <FieldGroup cols={1}>
        <Field label="Número do período" required error={errors.numero?.message}>
          <select className="fasi-input" {...register('numero', { valueAsNumber: true, required: 'Obrigatório' })}>
            {([1, 2, 3, 4] as const).map(n => <option key={n} value={n}>Período {n}</option>)}
          </select>
        </Field>
      </FieldGroup>
      <div className="flex gap-2 mt-3">
        <SubmitButton loading={loading} label={editing ? 'Salvar' : 'Adicionar'} />
        <button type="button" onClick={onCancel} className="fasi-btn-secondary text-sm px-4">Cancelar</button>
      </div>
    </form>
  )
}

function TabPeriodos({ tipo }: { tipo: TipoForm }) {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const { data: periodos = [], isLoading } = useQuery<Periodo[]>({
    queryKey: ['admin-periodos', tipo],
    queryFn: async () => {
      const { data } = await apiAuth.get(`/api/admin/periodos-submissao?tipo=${tipo}`)
      return (data as Periodo[]).filter(p => p.tipo === tipo)
    },
  })

  const createMutation = useMutation({
    mutationFn: (body: object) => apiAuth.post('/api/admin/periodos-submissao', body),
    onSuccess: () => {
      toast.success('Período criado!')
      qc.invalidateQueries({ queryKey: ['admin-periodos', tipo] })
      qc.invalidateQueries({ queryKey: ['periodos-submissao', tipo] })
      setShowForm(false)
    },
    onError: () => toast.error('Erro ao criar período'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) =>
      apiAuth.put(`/api/admin/periodos-submissao/${id}`, body),
    onSuccess: () => {
      toast.success('Período atualizado!')
      qc.invalidateQueries({ queryKey: ['admin-periodos', tipo] })
      qc.invalidateQueries({ queryKey: ['periodos-submissao', tipo] })
      setEditingId(null)
    },
    onError: () => toast.error('Erro ao atualizar período'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiAuth.delete(`/api/admin/periodos-submissao/${id}`),
    onSuccess: () => {
      toast.success('Período removido')
      qc.invalidateQueries({ queryKey: ['admin-periodos', tipo] })
      qc.invalidateQueries({ queryKey: ['periodos-submissao', tipo] })
    },
    onError: () => toast.error('Erro ao remover período'),
  })

  const handleSave = (data: PeriodoFormData & { tipo: TipoForm }) => {
    const payload = {
      tipo: data.tipo,
      numero: data.numero,
      data_inicio: data.data_inicio,
      data_fim: data.data_fim,
      semestre: data.semestre || null,
    }
    if (editingId !== null) {
      updateMutation.mutate({ id: editingId, body: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  if (isLoading) return <div className="flex justify-center py-8"><Loader2 className="animate-spin w-5 h-5 text-muted-foreground" /></div>

  return (
    <div>
      {periodos.length === 0 && !showForm && (
        <p className="text-sm text-muted-foreground py-4">Nenhum período cadastrado para {TIPO_LABELS[tipo]}.</p>
      )}

      {periodos.length > 0 && (
        <div className="space-y-2 mt-2">
          {periodos.map(p => {
            const status = getPeriodoStatus(p)
            return editingId === p.id ? (
              <PeriodoForm
                key={p.id}
                tipo={tipo}
                editing={p}
                onSave={handleSave}
                onCancel={() => setEditingId(null)}
                loading={updateMutation.isPending}
              />
            ) : (
              <div key={p.id} className="flex items-center justify-between border rounded-lg px-4 py-3 bg-background">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-medium text-sm">Período {p.numero}</span>
                  <span className="text-sm text-muted-foreground">
                    {formatDateBR(p.data_inicio)} → {formatDateBR(p.data_fim)}
                  </span>
                  {p.semestre && (
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">{p.semestre}</span>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${status.cls}`}>{status.label}</span>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => { setEditingId(p.id); setShowForm(false) }}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    title="Editar"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => { if (confirm('Remover este período?')) deleteMutation.mutate(p.id) }}
                    className="text-muted-foreground hover:text-destructive transition-colors"
                    title="Remover"
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showForm && editingId === null && (
        <PeriodoForm
          tipo={tipo}
          onSave={handleSave}
          onCancel={() => setShowForm(false)}
          loading={createMutation.isPending}
        />
      )}

      {!showForm && editingId === null && periodos.length < 4 && (
        <button
          onClick={() => setShowForm(true)}
          className="mt-3 flex items-center gap-1.5 text-sm text-fasi-600 hover:text-fasi-700 font-medium"
        >
          <Plus className="w-4 h-4" /> Adicionar período
        </button>
      )}
    </div>
  )
}

const TABS: TipoForm[] = ['tcc', 'acc', 'estagio', 'ccf']

export function GestorPeriodos() {
  const [activeTab, setActiveTab] = useState<TipoForm>('tcc')

  return (
    <PageShell icon="📅" title="Gestor de Períodos de Submissão"
      subtitle="Defina os períodos em que cada formulário pode ser submetido">
      <TokenGate storageKey="fasi_config_auth">
        <div className="fasi-info-box mb-6 text-sm">
          <strong>Como funciona:</strong> Cadastre até 4 períodos por formulário. Alunos só conseguem enviar
          dentro das datas configuradas. Para o <strong>Requerimento TCC</strong>, a data de defesa deve
          estar dentro de um período ativo.
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b mb-4">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === t
                  ? 'border-fasi-500 text-fasi-600'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Calendar className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              {TIPO_LABELS[t]}
            </button>
          ))}
        </div>

        <FormSection title={`Períodos — ${TIPO_LABELS[activeTab]}`}>
          <TabPeriodos key={activeTab} tipo={activeTab} />
        </FormSection>
      </TokenGate>
    </PageShell>
  )
}
