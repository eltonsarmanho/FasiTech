import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, Field } from '@/shared/components/FormSection'
import { FileUpload } from '@/shared/components/FileUpload'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { PROFESSORES } from '@/shared/lib/constants'
import { usePeriodosLetivos } from '@/shared/hooks/usePeriodosLetivos'
import { submitForm } from '@/shared/lib/api'

const schema = z.object({
  docente:       z.string().min(1, 'Docente obrigatório'),
  docente_outro: z.string().optional(),
  semestre:      z.string().min(1, 'Semestre obrigatório'),
})
type FormData = z.infer<typeof schema>

export function FormPlanoEnsino() {
  const [files, setFiles] = useState<File[]>([])
  const [fileKey, setFileKey] = useState(0)
  const [docenteSel, setDocenteSel] = useState('')
  const { data: periodos = [] } = usePeriodosLetivos()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (!files.length) throw new Error('Selecione pelo menos um arquivo')
      const fd = new FormData()
      const docenteFinal = data.docente === 'Outro:' ? (data.docente_outro ?? '') : data.docente
      fd.append('docente', docenteFinal)
      fd.append('semestre', data.semestre)
      files.forEach(f => fd.append('arquivos', f))
      return submitForm('/api/v1/forms/plano-ensino', fd)
    },
    onSuccess: () => { toast.success('Plano de ensino enviado com sucesso!'); reset(); setFiles([]); setFileKey(k => k + 1); setDocenteSel('') },
    onError: (e: Error) => toast.error(e.message || 'Erro ao enviar.'),
  })

  return (
    <PageShell icon="📚" title="Formulário de Plano de Ensino"
      subtitle="Submissão de Planos de Ensino por Disciplina">

      <div className="fasi-info-box mb-6">
        <p className="font-medium mb-1">Instruções importantes:</p>
        <ul className="list-disc pl-5 text-sm space-y-0.5">
          <li>Insira no formato <strong>Documento ou PDF</strong></li>
          <li>Coloque <strong>por semestre</strong></li>
          <li>Nome dos arquivos: <strong>[Docente] Plano de Ensino - Disciplina</strong></li>
        </ul>
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="Docente Responsável">
          <Field label="Nome do Docente" required error={errors.docente?.message}>
            <select
              className="fasi-input"
              {...register('docente')}
              onChange={e => setDocenteSel(e.target.value)}
            >
              <option value="">Selecione o docente...</option>
              {PROFESSORES.map(p => <option key={p} value={p}>{p}</option>)}
              <option value="Outro:">Outro:</option>
            </select>
          </Field>
          {docenteSel === 'Outro:' && (
            <Field label="Nome completo do docente" required error={errors.docente_outro?.message}>
              <input className="fasi-input" placeholder="Nome completo do docente" {...register('docente_outro')} />
            </Field>
          )}
        </FormSection>

        <FormSection title="Semestre">
          <Field label="Semestre" required error={errors.semestre?.message}>
            <select className="fasi-input" {...register('semestre')}>
              <option value="">Escolher...</option>
              {periodos.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
        </FormSection>

        <FormSection title="Arquivos do Plano de Ensino">
          <p className="text-sm text-muted-foreground mb-3">
            Faça upload de até 10 arquivos PDF. Tamanho máximo: 50 MB por arquivo.
          </p>
          <FileUpload
            key={fileKey}
            accept=".pdf"
            multiple
            maxSizeMB={50}
            label="Clique ou arraste os PDFs dos planos de ensino"
            onChange={setFiles}
            error={mutation.isError && !files.length ? 'Pelo menos um arquivo é obrigatório' : undefined}
          />
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar Plano de Ensino" />
      </form>
    </PageShell>
  )
}
