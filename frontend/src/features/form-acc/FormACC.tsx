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
import { POLOS_ACC } from '@/shared/lib/constants'
import { usePeriodosLetivos } from '@/shared/hooks/usePeriodosLetivos'
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

export function FormACC() {
  const [files, setFiles] = useState<File[]>([])
  const [fileKey, setFileKey] = useState(0)
  const { data: periodos = [] } = usePeriodosLetivos()
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (!files[0]) throw new Error('Selecione o arquivo PDF')
      const fd = new FormData()
      Object.entries(data).forEach(([k, v]) => fd.append(k, v))
      fd.append('arquivo_pdf', files[0])
      return submitForm('/api/v1/forms/acc', fd)
    },
    onSuccess: () => {
      toast.success('ACC enviada com sucesso! Você receberá confirmação por e-mail.')
      reset()
      setFiles([])
      setFileKey(k => k + 1)
    },
    onError: (e: Error) => toast.error(e.message || 'Erro ao enviar. Tente novamente.'),
  })

  return (
    <PageShell
      icon="🎓"
      title="Formulário de ACC"
      subtitle="Submissão de Atividades Complementares Curriculares"
    >
      <div className="fasi-info-box mb-6">
        Consolide todos os seus certificados em <strong>um único arquivo PDF</strong> antes de enviar.
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
                {POLOS_ACC.map(p => <option key={p} value={p}>{p}</option>)}
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

        <FormSection title="Arquivo PDF">
          <FileUpload
            key={fileKey}
            accept=".pdf"
            maxSizeMB={50}
            label="Clique ou arraste o PDF consolidado das ACCs"
            onChange={setFiles}
            error={mutation.isError && !files[0] ? 'Arquivo obrigatório' : undefined}
          />
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar ACC" loadingLabel="Enviando..." />
      </form>
    </PageShell>
  )
}
