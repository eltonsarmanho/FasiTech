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
import { POLOS, COMPONENTES_TCC } from '@/shared/lib/constants'
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
  componente: z.enum(COMPONENTES_TCC),
})
type FormData = z.infer<typeof schema>

export function FormTCC() {
  const [files, setFiles] = useState<File[]>([])
  const [fileKey, setFileKey] = useState(0)
  const { data: periodos = [] } = usePeriodosLetivos()
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })
  const componente = watch('componente')

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (!files.length) throw new Error('Selecione os arquivos PDF')
      if (data.componente === 'TCC 2' && files.length < 2)
        throw new Error('TCC 2 exige no mínimo 2 arquivos: TCC Final + Declaração de Autoria')
      const fd = new FormData()
      Object.entries(data).forEach(([k, v]) => fd.append(k, v))
      files.forEach(f => fd.append('arquivos', f))
      return submitForm('/api/v1/forms/tcc', fd)
    },
    onSuccess: () => { toast.success('TCC enviado com sucesso!'); reset(); setFiles([]); setFileKey(k => k + 1) },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <PageShell icon="📚" title="Formulário TCC"
      subtitle="Submissão do Trabalho de Conclusão de Curso — TCC 1 e TCC 2">
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
            <Field label="Período letivo" required error={errors.periodo?.message}>
              <select className="fasi-input" {...register('periodo')}>
                <option value="">Selecione</option>
                {periodos.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Informações do TCC">
          <FieldGroup cols={2}>
            <Field label="Orientador(a)" required error={errors.orientador?.message}>
              <input className="fasi-input" placeholder="Prof. Dr. Nome Sobrenome" {...register('orientador')} />
            </Field>
            <Field label="Componente curricular" required error={errors.componente?.message}>
              <select className="fasi-input" {...register('componente')}>
                <option value="">Selecione</option>
                {COMPONENTES_TCC.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Título do trabalho" required error={errors.titulo?.message} className="sm:col-span-2">
              <input className="fasi-input" {...register('titulo')} />
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Arquivos PDF">
          {componente === 'TCC 1' && (
            <div className="fasi-info-box mb-4">
              <p className="font-semibold mb-1">📘 TCC 1 — Documentos Obrigatórios:</p>
              <p className="text-sm mb-1">Anexe os seguintes arquivos:</p>
              <ul className="list-disc pl-5 text-sm space-y-0.5">
                <li>📄 ANEXO I das Diretrizes do TCC</li>
                <li>📄 ANEXO II das Diretrizes do TCC</li>
              </ul>
              <p className="text-sm mt-1 font-medium">Mínimo: 2 arquivos PDF</p>
            </div>
          )}
          {componente === 'TCC 2' && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 mb-4 text-amber-900 text-sm space-y-2">
              <p className="font-semibold">📗 TCC 2 — Documentos Obrigatórios:</p>
              <p>⚠️ <strong>ATENÇÃO:</strong> Para TCC 2, anexe:</p>
              <ol className="list-decimal pl-5 space-y-1">
                <li>📄 <strong>Versão Final do TCC</strong></li>
                <li>📄 <strong>Um PDF de Declaração de Autoria ou Termo de Autorização</strong></li>
              </ol>
              <p>Se você tiver os dois documentos separados ou juntos, também pode enviar sem problema.</p>
              <p>
                <strong>Modelo do Termo/Declaração: </strong>
                <a
                  href="https://drive.google.com/file/d/1Gsev2C_Rhc-IuA_TP-MdHiWXE4m9kwtx/view?usp=sharing"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline text-amber-800 hover:text-amber-600"
                >
                  Baixar modelo
                </a>
              </p>
              <p className="font-medium">Mínimo: 2 arquivos PDF</p>
              <p>💡 <strong>Importante:</strong> A biblioteca (<a href="mailto:bibcameta@ufpa.br" className="underline">bibcameta@ufpa.br</a>) receberá uma cópia da sua submissão.</p>
            </div>
          )}
          <FileUpload
            key={fileKey}
            accept=".pdf"
            multiple
            maxSizeMB={50}
            label={componente === 'TCC 2' ? 'Selecione os PDFs do TCC 2 (mín. 2 arquivos)' : 'Selecione os PDFs do TCC 1 (mín. 2 arquivos)'}
            onChange={setFiles}
          />
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar TCC" loadingLabel="Enviando..." />
      </form>
    </PageShell>
  )
}
