import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Trash2, Loader2, Bell, Send, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { apiAuth } from '@/shared/lib/api'
import { formatDate } from '@/shared/lib/utils'

interface Alerta {
  id: number
  titulo: string
  descricao: string
  data_inicio: string
  data_fim: string
  horario_disparo: string
  ativo: boolean
  destination_type: string
  destination_emails?: string
  ultimo_disparo?: string
}

type AlertStatus = 'active' | 'inactive' | 'expired' | 'waiting'

function getAlertStatus(a: Alerta): AlertStatus {
  if (!a.ativo) return 'inactive'
  const today = new Date().toISOString().slice(0, 10)
  if (a.data_fim < today) return 'expired'
  if (a.data_inicio > today) return 'waiting'
  return 'active'
}

const STATUS_LABEL: Record<AlertStatus, string> = {
  active: 'Ativo',
  inactive: 'Inativo',
  expired: 'Expirado',
  waiting: 'Aguardando',
}

const STATUS_CLASS: Record<AlertStatus, string> = {
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-muted text-muted-foreground',
  expired: 'bg-blue-100 text-blue-700',
  waiting: 'bg-yellow-100 text-yellow-700',
}

function AlertaForm({
  defaultValues,
  onSubmit,
  loading,
  submitLabel,
}: {
  defaultValues?: Partial<Alerta>
  onSubmit: (data: object) => void
  loading: boolean
  submitLabel: string
}) {
  const { register, handleSubmit } = useForm({ defaultValues })
  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <FieldGroup cols={2}>
        <Field label="Título" required className="sm:col-span-2">
          <input className="fasi-input" {...register('titulo', { required: true })} />
        </Field>
        <Field label="Descrição / Mensagem" required className="sm:col-span-2">
          <textarea className="fasi-input min-h-[80px]" {...register('descricao', { required: true })} />
        </Field>
        <Field label="Data de início" required>
          <input className="fasi-input" type="date" {...register('data_inicio', { required: true })} />
        </Field>
        <Field label="Data de fim" required>
          <input className="fasi-input" type="date" {...register('data_fim', { required: true })} />
        </Field>
        <Field label="Horário de disparo" required>
          <input className="fasi-input" type="time" {...register('horario_disparo', { required: true })} />
        </Field>
        <Field label="Destinatários">
          <select className="fasi-input" {...register('destination_type')}>
            <option value="docentes">Docentes</option>
            <option value="externos">E-mails específicos</option>
          </select>
        </Field>
        <Field label="E-mails (se específicos)" hint="separados por ponto e vírgula" className="sm:col-span-2">
          <input className="fasi-input" placeholder="a@ufpa.br; b@ufpa.br" {...register('destination_emails')} />
        </Field>
        <Field label="Ativo" className="sm:col-span-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" {...register('ativo')} defaultChecked className="w-4 h-4" />
            <span className="text-sm">Ativar gatilho imediatamente</span>
          </label>
        </Field>
      </FieldGroup>
      <div className="mt-4">
        <SubmitButton loading={loading} label={submitLabel} />
      </div>
    </form>
  )
}

export function GestorAlertas() {
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const qc = useQueryClient()

  const { data: alertas = [], isLoading } = useQuery<Alerta[]>({
    queryKey: ['alertas'],
    queryFn: async () => (await apiAuth.get('/api/admin/alertas')).data,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiAuth.delete(`/api/admin/alertas/${id}`),
    onSuccess: () => { toast.success('Alerta removido'); qc.invalidateQueries({ queryKey: ['alertas'] }) },
    onError: () => toast.error('Erro ao remover'),
  })

  const createMutation = useMutation({
    mutationFn: (data: object) => apiAuth.post('/api/admin/alertas', data),
    onSuccess: () => {
      toast.success('Alerta criado!')
      qc.invalidateQueries({ queryKey: ['alertas'] })
      setCreating(false)
    },
    onError: () => toast.error('Erro ao criar alerta'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: object }) =>
      apiAuth.put(`/api/admin/alertas/${id}`, data),
    onSuccess: () => {
      toast.success('Alerta atualizado!')
      qc.invalidateQueries({ queryKey: ['alertas'] })
      setEditingId(null)
    },
    onError: () => toast.error('Erro ao atualizar alerta'),
  })

  const dispararMutation = useMutation({
    mutationFn: (id: number) => apiAuth.post(`/api/admin/alertas/${id}/disparar`),
    onSuccess: (res) => toast.success(res.data?.message ?? 'Alerta disparado!'),
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? 'Erro ao disparar'),
  })

  const ativos = alertas.filter(a => getAlertStatus(a) === 'active').length

  return (
    <PageShell icon="🔔" title="Gestor de Alertas Acadêmicos"
      subtitle="Configure gatilhos de e-mail automáticos para docentes e discentes">

      {/* Métricas */}
      {alertas.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            { label: 'Total', value: alertas.length },
            { label: 'Ativos', value: ativos },
            { label: 'Inativos / Expirados', value: alertas.length - ativos },
          ].map(({ label, value }) => (
            <div key={label} className="fasi-card p-4 text-center">
              <p className="text-2xl font-bold text-fasi-600">{value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mb-4 flex justify-end">
        <button onClick={() => { setCreating(v => !v); setEditingId(null) }} className="fasi-btn-primary">
          <Plus className="w-4 h-4" />
          {creating ? 'Cancelar' : 'Novo Alerta'}
        </button>
      </div>

      {creating && (
        <FormSection title="Novo Alerta">
          <AlertaForm
            onSubmit={d => createMutation.mutate(d)}
            loading={createMutation.isPending}
            submitLabel="Criar Alerta"
          />
        </FormSection>
      )}

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-fasi-500" />
        </div>
      )}

      {!isLoading && alertas.length === 0 && (
        <div className="fasi-info-box">Nenhum alerta configurado.</div>
      )}

      <div className="space-y-3">
        {alertas.map(alerta => {
          const st = getAlertStatus(alerta)
          const isEditing = editingId === alerta.id

          return (
            <div key={alerta.id} className="fasi-card p-4">
              {isEditing ? (
                <>
                  <p className="font-semibold text-sm mb-3 text-fasi-700">Editando: {alerta.titulo}</p>
                  <AlertaForm
                    defaultValues={alerta}
                    onSubmit={d => updateMutation.mutate({ id: alerta.id, data: d })}
                    loading={updateMutation.isPending}
                    submitLabel="Salvar Alterações"
                  />
                  <button className="fasi-btn-outline mt-2 py-1 px-3 text-sm"
                    onClick={() => setEditingId(null)}>
                    Cancelar
                  </button>
                </>
              ) : (
                <div className="flex items-start gap-4">
                  <Bell className={`w-5 h-5 mt-0.5 shrink-0 ${st === 'active' ? 'text-fasi-500' : 'text-muted-foreground'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="font-semibold text-sm text-foreground">{alerta.titulo}</span>
                      <span className={`fasi-badge ${STATUS_CLASS[st]}`}>{STATUS_LABEL[st]}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-1 line-clamp-2">{alerta.descricao}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(alerta.data_inicio)} → {formatDate(alerta.data_fim)}
                      {' • '}{alerta.horario_disparo}
                      {' • '}{alerta.destination_type === 'externos' ? 'E-mails específicos' : 'Docentes'}
                      {alerta.ultimo_disparo && (
                        <> • Último disparo: {formatDate(alerta.ultimo_disparo)}</>
                      )}
                    </p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button
                      onClick={() => dispararMutation.mutate(alerta.id)}
                      disabled={dispararMutation.isPending}
                      className="text-muted-foreground hover:text-fasi-600 transition-colors p-1"
                      title="Disparar alerta agora"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => { setEditingId(alerta.id); setCreating(false) }}
                      className="text-muted-foreground hover:text-fasi-600 transition-colors p-1"
                      title="Editar alerta"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(alerta.id)}
                      disabled={deleteMutation.isPending}
                      className="text-muted-foreground hover:text-red-500 transition-colors p-1"
                      title="Excluir alerta"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </PageShell>
  )
}
