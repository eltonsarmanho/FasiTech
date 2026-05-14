import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { FileUpload } from '@/shared/components/FileUpload'
import { SubmitButton } from '@/shared/components/SubmitButton'
import {
  PROFESSORES,
  NATUREZAS_PROJETO,
  SOLICITACOES_PROJETO,
  EDITAIS_PROJETO,
  CARGAS_HORARIAS_PROJETO,
} from '@/shared/lib/constants'
import { submitForm } from '@/shared/lib/api'
import { numericProps, ANO_REGEX, ANO_MSG } from '@/shared/lib/masks'

const CURRENT_YEAR = new Date().getFullYear().toString()

const schema = z.object({
  docente:       z.string().min(1, 'Docente obrigatório'),
  parecerista1:  z.string().min(1, 'Parecerista 1 obrigatório'),
  parecerista2:  z.string().min(1, 'Parecerista 2 obrigatório'),
  nome_projeto:  z.string().min(3, 'Nome do projeto obrigatório'),
  natureza:      z.string().min(1, 'Natureza obrigatória'),
  solicitacao:   z.string().min(1, 'Tipo de solicitação obrigatório'),
  edital:        z.string().min(1, 'Edital obrigatório'),
  ano_edital:    z.string().regex(ANO_REGEX, ANO_MSG),
  carga_horaria: z.string().min(1, 'Carga horária obrigatória'),
})
type FormData = z.infer<typeof schema>

export function FormProjetos() {
  const [files, setFiles] = useState<File[]>([])
  const [fileKey, setFileKey] = useState(0)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { ano_edital: CURRENT_YEAR },
  })

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      const fd = new FormData()
      Object.entries(data).forEach(([k, v]) => fd.append(k, v))
      files.forEach(f => fd.append('arquivos', f))
      return submitForm('/api/v1/forms/projetos', fd)
    },
    onSuccess: () => { toast.success('Projeto enviado com sucesso!'); reset({ ano_edital: CURRENT_YEAR }); setFiles([]); setFileKey(k => k + 1) },
    onError: () => toast.error('Erro ao enviar. Tente novamente.'),
  })

  return (
    <PageShell icon="🔬" title="Formulário de Projetos"
      subtitle="Registro de Projetos de Ensino, Pesquisa e Extensão">
      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="Dados do Projeto">
          <FieldGroup cols={2}>
            <Field label="Docente responsável" required error={errors.docente?.message}>
              <select className="fasi-input" {...register('docente')}>
                <option value="">Selecione o docente...</option>
                {PROFESSORES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Nome do projeto" required error={errors.nome_projeto?.message} className="sm:col-span-2">
              <input className="fasi-input" placeholder="Título completo do projeto" {...register('nome_projeto')} />
            </Field>
            <Field label="Natureza" required error={errors.natureza?.message}>
              <select className="fasi-input" {...register('natureza')}>
                <option value="">Selecione</option>
                {NATUREZAS_PROJETO.map(n => <option key={n}>{n}</option>)}
              </select>
            </Field>
            <Field label="Solicitação" required error={errors.solicitacao?.message}>
              <select className="fasi-input" {...register('solicitacao')}>
                <option value="">Selecione</option>
                {SOLICITACOES_PROJETO.map(s => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Edital" required error={errors.edital?.message}>
              <select className="fasi-input" {...register('edital')}>
                <option value="">Selecione o edital</option>
                {EDITAIS_PROJETO.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
            </Field>
            <Field label="Ano do Edital" required error={errors.ano_edital?.message}>
              <input className="fasi-input" placeholder="2026" {...numericProps(4)} {...register('ano_edital')} />
            </Field>
            <Field label="Carga horária semanal" required error={errors.carga_horaria?.message}>
              <select className="fasi-input" {...register('carga_horaria')}>
                <option value="">Selecione</option>
                {CARGAS_HORARIAS_PROJETO.map(c => <option key={c} value={c}>{c}h</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Pareceristas">
          <FieldGroup cols={2}>
            <Field label="Parecerista 1" required error={errors.parecerista1?.message}>
              <select className="fasi-input" {...register('parecerista1')}>
                <option value="">Selecione o parecerista 1</option>
                {PROFESSORES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Parecerista 2" required error={errors.parecerista2?.message}>
              <select className="fasi-input" {...register('parecerista2')}>
                <option value="">Selecione o parecerista 2</option>
                {PROFESSORES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Arquivos do Projeto">
          <FileUpload
            key={fileKey}
            accept=".pdf"
            multiple
            maxSizeMB={50}
            label="Selecione os documentos do projeto (PDF)"
            onChange={setFiles}
          />
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar Projeto" />
      </form>
    </PageShell>
  )
}
