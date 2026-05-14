import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useState } from 'react'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { FileUpload } from '@/shared/components/FileUpload'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { POLOS, COMPONENTES_ESTAGIO } from '@/shared/lib/constants'
import { usePeriodosLetivos } from '@/shared/hooks/usePeriodosLetivos'
import { submitForm } from '@/shared/lib/api'
import { numericProps, MATRICULA_REGEX, MATRICULA_MSG, ANO_REGEX, ANO_MSG, EMAIL_MSG } from '@/shared/lib/masks'

const schema = z.object({
  nome:       z.string().min(3, 'Nome é obrigatório'),
  matricula:  z.string().regex(MATRICULA_REGEX, MATRICULA_MSG),
  email:      z.string().email(EMAIL_MSG),
  turma:      z.string().regex(ANO_REGEX, ANO_MSG),
  polo:       z.string().min(1, 'Polo é obrigatório'),
  periodo:    z.string().min(1, 'Período é obrigatório'),
  orientador: z.string().min(3, 'Nome do orientador é obrigatório'),
  titulo:     z.string().min(5, 'Título é obrigatório'),
  componente: z.string().min(1, 'Componente é obrigatório'),
})
type FormData = z.infer<typeof schema>

export function FormEstagio() {
  const [files, setFiles] = useState<File[]>([])
  const [fileKey, setFileKey] = useState(0)
  const { data: periodos = [] } = usePeriodosLetivos()
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (!files.length) throw new Error('Selecione os arquivos')
      const fd = new FormData()
      Object.entries(data).forEach(([k, v]) => fd.append(k, v))
      files.forEach(f => fd.append('arquivos', f))
      return submitForm('/api/v1/forms/estagio', fd)
    },
    onSuccess: () => { toast.success('Estágio enviado com sucesso!'); reset(); setFiles([]); setFileKey(k => k + 1) },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <PageShell icon="📋" title="Formulário de Estágio"
      subtitle="Envio de documentos de Estágio I e II">
      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="Dados do Discente">
          <FieldGroup cols={2}>
            <Field label="Nome" required error={errors.nome?.message}>
              <input className="fasi-input" {...register('nome')} />
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
                <option value="">Selecione</option>
                {POLOS.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Período" required error={errors.periodo?.message}>
              <select className="fasi-input" {...register('periodo')}>
                <option value="">Selecione</option>
                {periodos.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Informações do Estágio">
          <div className="fasi-info-box mb-4 text-sm space-y-1">
            <p className="font-semibold mb-1">ℹ️ Informações sobre Componente Curricular:</p>
            <ul className="space-y-0.5 pl-1">
              <li>• <strong>Plano de Estágio</strong> → Refere-se ao Estágio I</li>
              <li>• <strong>Relatório Final</strong> → Refere-se ao Estágio II</li>
              <li>• <strong>Relatório Estágio I ou II</strong> → Refere-se ao Estágio I ou II para Alunos do PPC Vigente</li>
            </ul>
          </div>
          <FieldGroup cols={2}>
            <Field label="Orientador(a)" required error={errors.orientador?.message}>
              <input className="fasi-input" {...register('orientador')} />
            </Field>
            <Field label="Componente" required error={errors.componente?.message}>
              <select className="fasi-input" {...register('componente')}>
                <option value="">Selecione</option>
                {COMPONENTES_ESTAGIO.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Título / Empresa" required error={errors.titulo?.message} className="sm:col-span-2">
              <input className="fasi-input" placeholder="Nome da empresa ou título do projeto" {...register('titulo')} />
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Arquivos">
          <FileUpload key={fileKey} accept=".pdf" multiple maxSizeMB={50}
            label="Selecione os documentos de estágio (PDF)" onChange={setFiles} />
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar Estágio" loadingLabel="Enviando..." />
      </form>
    </PageShell>
  )
}
