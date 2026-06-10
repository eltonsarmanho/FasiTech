import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Trash2, Loader2, Pencil, Mail, Phone, Cake } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { TokenGate } from '@/shared/components/TokenGate'
import { apiAuth } from '@/shared/lib/api'

const TITULOS = ['Doutorado', 'Mestrado', 'Especialista', 'Graduação'] as const
const TIPOS = ['Interno', 'Externo'] as const
const CATEGORIAS = ['Docente', 'Secretaria', 'Colaborador'] as const

// Cargos/funções na faculdade (flags booleanas)
const CARGOS = [
  { key: 'diretor_faculdade', label: 'Diretor da Faculdade' },
  { key: 'coordenador_estagio', label: 'Coordenador de Estágio' },
  { key: 'representante_docente', label: 'Representante Docente' },
] as const

type Titulo = (typeof TITULOS)[number]
type Tipo = (typeof TIPOS)[number]
type Categoria = (typeof CATEGORIAS)[number]

interface Funcionario {
  id: number
  nome: string
  filiacao: string | null
  titulo: string
  tipo: string
  categoria: string
  email: string | null
  fone: string | null
  data_aniversario: string | null
  diretor_faculdade: boolean
  coordenador_estagio: boolean
  representante_docente: boolean
}

interface FuncionarioFormData {
  nome: string
  filiacao: string
  titulo: Titulo
  tipo: Tipo
  categoria: Categoria
  email: string
  fone: string
  data_aniversario: string
  diretor_faculdade: boolean
  coordenador_estagio: boolean
  representante_docente: boolean
}

function formatDateBR(iso: string | null) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function FuncionarioForm({
  editing,
  onSave,
  onCancel,
  loading,
}: {
  editing?: Funcionario
  onSave: (data: FuncionarioFormData) => void
  onCancel: () => void
  loading: boolean
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FuncionarioFormData>({
    defaultValues: editing
      ? {
          nome: editing.nome,
          filiacao: editing.filiacao ?? '',
          titulo: (editing.titulo as Titulo) ?? 'Graduação',
          tipo: (editing.tipo as Tipo) ?? 'Interno',
          categoria: (editing.categoria as Categoria) ?? 'Docente',
          email: editing.email ?? '',
          fone: editing.fone ?? '',
          data_aniversario: editing.data_aniversario ?? '',
          diretor_faculdade: editing.diretor_faculdade ?? false,
          coordenador_estagio: editing.coordenador_estagio ?? false,
          representante_docente: editing.representante_docente ?? false,
        }
      : {
          nome: '', filiacao: '', titulo: 'Graduação', tipo: 'Interno', categoria: 'Docente',
          email: '', fone: '', data_aniversario: '',
          diretor_faculdade: false, coordenador_estagio: false, representante_docente: false,
        },
  })

  return (
    <form onSubmit={handleSubmit(onSave)} className="border rounded-lg p-4 bg-muted/30 mt-4">
      <p className="font-semibold text-sm mb-3">{editing ? 'Editar funcionário' : 'Novo funcionário'}</p>
      <FieldGroup cols={2}>
        <Field label="Nome" required error={errors.nome?.message}>
          <input className="fasi-input" {...register('nome', { required: 'Obrigatório' })} />
        </Field>
        <Field label="Filiação">
          <input className="fasi-input" placeholder="Nome do pai/mãe" {...register('filiacao')} />
        </Field>
        <Field label="Título" required error={errors.titulo?.message}>
          <select className="fasi-input" {...register('titulo', { required: 'Obrigatório' })}>
            {TITULOS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="Tipo" required error={errors.tipo?.message}>
          <select className="fasi-input" {...register('tipo', { required: 'Obrigatório' })}>
            {TIPOS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="Categoria" required error={errors.categoria?.message}>
          <select className="fasi-input" {...register('categoria', { required: 'Obrigatório' })}>
            {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="E-mail" error={errors.email?.message}>
          <input
            className="fasi-input"
            type="email"
            placeholder="exemplo@dominio.com"
            {...register('email', {
              pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'E-mail inválido' },
            })}
          />
        </Field>
        <Field label="Fone (WhatsApp)">
          <input className="fasi-input" placeholder="(00) 00000-0000" {...register('fone')} />
        </Field>
        <Field label="Data de aniversário">
          <input className="fasi-input" type="date" {...register('data_aniversario')} />
        </Field>
      </FieldGroup>

      <div className="mt-4">
        <p className="text-sm font-medium text-foreground mb-2">Cargos / Funções na Faculdade</p>
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3">
          {CARGOS.map(c => (
            <label key={c.key} className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" className="h-4 w-4 rounded border-input accent-fasi-500" {...register(c.key)} />
              {c.label}
            </label>
          ))}
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <SubmitButton loading={loading} label={editing ? 'Salvar' : 'Adicionar'} />
        <button type="button" onClick={onCancel} className="fasi-btn-secondary text-sm px-4">Cancelar</button>
      </div>
    </form>
  )
}

function tipoBadge(tipo: string) {
  return tipo === 'Interno'
    ? 'bg-green-100 text-green-700'
    : 'bg-blue-100 text-blue-700'
}

export function GestorFuncionarios() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const { data: funcionarios = [], isLoading } = useQuery<Funcionario[]>({
    queryKey: ['admin-funcionarios'],
    queryFn: async () => {
      const { data } = await apiAuth.get('/api/admin/funcionarios')
      return data as Funcionario[]
    },
  })

  const createMutation = useMutation({
    mutationFn: (body: object) => apiAuth.post('/api/admin/funcionarios', body),
    onSuccess: () => {
      toast.success('Funcionário criado!')
      qc.invalidateQueries({ queryKey: ['admin-funcionarios'] })
      setShowForm(false)
    },
    onError: () => toast.error('Erro ao criar funcionário'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) =>
      apiAuth.put(`/api/admin/funcionarios/${id}`, body),
    onSuccess: () => {
      toast.success('Funcionário atualizado!')
      qc.invalidateQueries({ queryKey: ['admin-funcionarios'] })
      setEditingId(null)
    },
    onError: () => toast.error('Erro ao atualizar funcionário'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiAuth.delete(`/api/admin/funcionarios/${id}`),
    onSuccess: () => {
      toast.success('Funcionário removido')
      qc.invalidateQueries({ queryKey: ['admin-funcionarios'] })
    },
    onError: () => toast.error('Erro ao remover funcionário'),
  })

  const handleSave = (data: FuncionarioFormData) => {
    const payload = {
      nome: data.nome,
      filiacao: data.filiacao || null,
      titulo: data.titulo,
      tipo: data.tipo,
      categoria: data.categoria,
      email: data.email || null,
      fone: data.fone || null,
      data_aniversario: data.data_aniversario || null,
      diretor_faculdade: data.diretor_faculdade,
      coordenador_estagio: data.coordenador_estagio,
      representante_docente: data.representante_docente,
    }
    if (editingId !== null) {
      updateMutation.mutate({ id: editingId, body: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  return (
    <PageShell icon="👥" title="Gerenciamento de Funcionário"
      subtitle="Cadastro de docentes e colaboradores da FASI">
      <TokenGate storageKey="fasi_config_auth">
        <FormSection title="Funcionários">
          {isLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="animate-spin w-5 h-5 text-muted-foreground" /></div>
          ) : (
            <div>
              {funcionarios.length === 0 && !showForm && (
                <p className="text-sm text-muted-foreground py-4">Nenhum funcionário cadastrado.</p>
              )}

              {funcionarios.length > 0 && (
                <div className="space-y-2 mt-2">
                  {funcionarios.map(f =>
                    editingId === f.id ? (
                      <FuncionarioForm
                        key={f.id}
                        editing={f}
                        onSave={handleSave}
                        onCancel={() => setEditingId(null)}
                        loading={updateMutation.isPending}
                      />
                    ) : (
                      <div key={f.id} className="flex items-start justify-between border rounded-lg px-4 py-3 bg-background">
                        <div className="flex flex-col gap-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-sm">{f.nome}</span>
                            <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">{f.titulo}</span>
                            <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">{f.categoria}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tipoBadge(f.tipo)}`}>{f.tipo}</span>
                          </div>
                          {CARGOS.some(c => f[c.key]) && (
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {CARGOS.filter(c => f[c.key]).map(c => (
                                <span key={c.key} className="text-xs px-2 py-0.5 rounded-full font-medium bg-amber-100 text-amber-700">
                                  {c.label}
                                </span>
                              ))}
                            </div>
                          )}
                          {f.filiacao && (
                            <span className="text-xs text-muted-foreground">Filiação: {f.filiacao}</span>
                          )}
                          <div className="flex items-center gap-4 flex-wrap text-xs text-muted-foreground">
                            {f.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{f.email}</span>}
                            {f.fone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{f.fone}</span>}
                            {f.data_aniversario && <span className="flex items-center gap-1"><Cake className="w-3 h-3" />{formatDateBR(f.data_aniversario)}</span>}
                          </div>
                        </div>
                        <div className="flex gap-2 shrink-0 ml-3">
                          <button
                            onClick={() => { setEditingId(f.id); setShowForm(false) }}
                            className="text-muted-foreground hover:text-foreground transition-colors"
                            title="Editar"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => { if (confirm('Remover este funcionário?')) deleteMutation.mutate(f.id) }}
                            className="text-muted-foreground hover:text-destructive transition-colors"
                            title="Remover"
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    )
                  )}
                </div>
              )}

              {showForm && editingId === null && (
                <FuncionarioForm
                  onSave={handleSave}
                  onCancel={() => setShowForm(false)}
                  loading={createMutation.isPending}
                />
              )}

              {!showForm && editingId === null && (
                <button
                  onClick={() => setShowForm(true)}
                  className="mt-3 flex items-center gap-1.5 text-sm text-fasi-600 hover:text-fasi-700 font-medium"
                >
                  <Plus className="w-4 h-4" /> Adicionar funcionário
                </button>
              )}
            </div>
          )}
        </FormSection>
      </TokenGate>
    </PageShell>
  )
}
