import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { ApiError } from '@/shared/lib/api'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { FileUpload } from '@/shared/components/FileUpload'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { POLOS } from '@/shared/lib/constants'
import { usePeriodosLetivos } from '@/shared/hooks/usePeriodosLetivos'
import { usePeriodosSubmissao, isPeriodoAtivo, formatPeriodo } from '@/shared/hooks/usePeriodosSubmissao'
import { submitForm } from '@/shared/lib/api'
import { numericProps, MATRICULA_REGEX, MATRICULA_MSG, ANO_REGEX, ANO_MSG, EMAIL_MSG } from '@/shared/lib/masks'

const schema = z.object({
  nome:      z.string().min(3, 'Nome é obrigatório'),
  matricula: z.string().regex(MATRICULA_REGEX, MATRICULA_MSG),
  email:     z.string().email(EMAIL_MSG),
  turma:     z.string().regex(ANO_REGEX, ANO_MSG),
  polo:      z.string().min(1, 'Polo é obrigatório'),
  periodo:   z.string().min(1, 'Período é obrigatório'),
})
type FormData = z.infer<typeof schema>

export function FormCCF() {
  const [files, setFiles] = useState<File[]>([])
  const [fileKey, setFileKey] = useState(0)
  const [jaEnviado, setJaEnviado] = useState(false)
  const [disciplinas, setDisciplinas] = useState<string[]>(['', '', '', '', ''])
  const { data: periodos = [] } = usePeriodosLetivos()
  const { data: periodosSubmissao = [] } = usePeriodosSubmissao('ccf')

  const hoje = new Date().toISOString().slice(0, 10)
  const periodoAberto = periodosSubmissao.length === 0 || isPeriodoAtivo(periodosSubmissao, hoje)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (!files[0]) throw new Error('Selecione o arquivo PDF')
      const fd = new FormData()
      Object.entries(data).forEach(([k, v]) => fd.append(k, v))
      fd.append('arquivo_pdf', files[0])
      disciplinas
        .map(d => d.trim())
        .filter(Boolean)
        .forEach(d => fd.append('disciplinas', d))
      return submitForm('/api/v1/forms/ccf', fd)
    },
    onSuccess: () => {
      toast.success('CCF enviado com sucesso! Você receberá confirmação por e-mail.')
      reset()
      setFiles([])
      setFileKey(k => k + 1)
      setDisciplinas(['', '', '', '', ''])
    },
    onError: (e: Error) => {
      if (e instanceof ApiError && e.status === 409) {
        setJaEnviado(true)
        toast.error(e.message)
      } else {
        toast.error(e.message || 'Erro ao enviar. Tente novamente.')
      }
    },
  })

  return (
    <PageShell
      icon="📑"
      title="Componentes Curriculares Flexibilizados (CCF)"
      subtitle="Submissão de Componentes Curriculares Flexibilizados"
    >
      {periodosSubmissao.length > 0 && (
        <div className={`mb-4 text-sm rounded-lg border p-3 ${periodoAberto ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}`}>
          {periodoAberto ? (
            <>
              <p className="font-semibold mb-1">Submissão aberta</p>
              <ul className="space-y-0.5">
                {periodosSubmissao.filter(p => {
                  const h = new Date().toISOString().slice(0, 10)
                  return p.data_inicio <= h && h <= p.data_fim
                }).map(p => (
                  <li key={p.id}>• Período {p.numero}: {formatPeriodo(p)}</li>
                ))}
              </ul>
            </>
          ) : (
            <>
              <p className="font-semibold mb-1">Submissão encerrada no momento</p>
              <p className="mb-1">Períodos de submissão disponíveis:</p>
              <ul className="space-y-0.5">
                {periodosSubmissao.map(p => (
                  <li key={p.id}>• Período {p.numero}: {formatPeriodo(p)}{p.semestre ? ` (${p.semestre})` : ''}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {jaEnviado && (
        <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-800">
          <p className="font-semibold">Envio já registrado</p>
          <p className="mt-1 text-sm">
            Seu CCF para este período letivo já foi enviado e está registrado no sistema.
            Não é permitido um segundo envio. Em caso de dúvidas, entre em contato com a secretaria.
          </p>
        </div>
      )}

      <div className="fasi-info-box mb-6">
        Consolide todos os comprovantes das suas atividades em <strong>um único arquivo PDF</strong> antes de enviar.
        Documentos soltos não serão aceitos.
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="Dados do Discente">
          <FieldGroup cols={2}>
            <Field label="Nome completo" required error={errors.nome?.message}>
              <input className="fasi-input" placeholder="Seu nome completo" {...register('nome')} />
            </Field>
            <Field label="Matrícula" required error={errors.matricula?.message}>
              <input className="fasi-input" placeholder="202116040006" {...numericProps(12)} {...register('matricula')} />
            </Field>
            <Field label="E-mail" required error={errors.email?.message}>
              <input className="fasi-input" type="email" placeholder="seu@email.com" {...register('email')} />
            </Field>
            <Field label="Ano de ingresso (Turma)" required error={errors.turma?.message}>
              <input className="fasi-input" placeholder="2026" {...numericProps(4)} {...register('turma')} />
            </Field>
            <Field label="Polo" required error={errors.polo?.message}>
              <select className="fasi-input" {...register('polo')}>
                <option value="">Selecione o polo</option>
                {POLOS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Período letivo" required error={errors.periodo?.message}>
              <select className="fasi-input" {...register('periodo')}>
                <option value="">Selecione o período</option>
                {periodos.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Disciplinas Flexibilizadas">
          <p className="text-xs text-muted-foreground mb-3">
            Informe os nomes das disciplinas flexibilizadas para que a secretaria/direção
            possa conferi-las com o PDF anexado. Adicione quantas forem necessárias.
          </p>
          <div className="space-y-2">
            {disciplinas.map((valor, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input
                  className="fasi-input flex-1"
                  placeholder={`Disciplina ${i + 1}`}
                  value={valor}
                  onChange={e => setDisciplinas(prev => prev.map((d, idx) => idx === i ? e.target.value : d))}
                />
                <button
                  type="button"
                  onClick={() => setDisciplinas(prev => prev.filter((_, idx) => idx !== i))}
                  className="p-2 rounded hover:bg-gray-100 text-muted-foreground hover:text-red-600 transition-colors shrink-0"
                  title="Remover disciplina"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setDisciplinas(prev => [...prev, ''])}
            className="mt-3 flex items-center gap-1.5 text-sm text-fasi-600 hover:text-fasi-700 font-medium"
          >
            <Plus className="w-4 h-4" /> Adicionar disciplina
          </button>
        </FormSection>

        <FormSection title="Arquivo PDF">
          <FileUpload
            key={fileKey}
            accept=".pdf"
            maxSizeMB={50}
            label="Clique ou arraste o PDF consolidado das atividades"
            onChange={setFiles}
            error={mutation.isError && !files[0] ? 'Arquivo obrigatório' : undefined}
          />
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar CCF" loadingLabel="Enviando..." disabled={!periodoAberto || mutation.isPending || jaEnviado} />
      </form>
    </PageShell>
  )
}
