import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Upload, FileText, X } from 'lucide-react'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { api } from '@/shared/lib/api'
import { numericProps, cpfProps, MATRICULA_REGEX, MATRICULA_MSG, CPF_REGEX, CPF_MSG, EMAIL_MSG } from '@/shared/lib/masks'

const TIPOS_DOCUMENTO = [
  { value: 'conclusao',       label: 'Comprovante de Conclusão de Curso' },
  { value: 'matricula_ativa', label: 'Comprovante de Matrícula Ativa' },
] as const

const schema = z.object({
  matricula:      z.string().regex(MATRICULA_REGEX, MATRICULA_MSG),
  cpf:            z.string().regex(CPF_REGEX, CPF_MSG),
  email:          z.string().email(EMAIL_MSG),
  tipo_documento: z.string().min(1, 'Selecione o tipo de documento.'),
})

type FormValues = z.infer<typeof schema>

export function FormEmissaoDocumentos() {
  const [historico, setHistorico] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (!historico) throw new Error('Histórico acadêmico é obrigatório.')

      const fd = new FormData()
      fd.append('matricula',      values.matricula)
      fd.append('cpf',            values.cpf)
      fd.append('email',          values.email)
      fd.append('tipo_documento', values.tipo_documento)
      fd.append('historico',      historico, historico.name)

      const { data } = await api.post('/api/v1/forms/emissao-documentos', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: (data) => {
      toast.success(data?.message ?? 'Documento emitido! Verifique seu e-mail.')
      reset()
      setHistorico(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      toast.error(detail ?? 'Erro ao processar. Tente novamente.')
    },
  })

  const handleFile = (file: File | null) => {
    if (!file) return
    if (file.type !== 'application/pdf') {
      toast.error('Apenas arquivos PDF são aceitos.')
      return
    }
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Arquivo excede o limite de 50 MB.')
      return
    }
    setHistorico(file)
  }

  return (
    <PageShell icon="📄" title="Emissão de Documentos"
      subtitle="Solicite comprovantes acadêmicos com validação automática do histórico">

      <div className="fasi-info-box mb-6 space-y-1">
        <p className="font-medium">Como funciona:</p>
        <ol className="list-decimal pl-5 text-sm space-y-0.5">
          <li>Informe matrícula, CPF e e-mail para envio do comprovante.</li>
          <li>Selecione o tipo de documento desejado.</li>
          <li>Anexe <strong>um único PDF do histórico acadêmico</strong> (máx. 50 MB).</li>
        </ol>
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="Seus dados">
          <FieldGroup cols={2}>
            <Field label="Matrícula" required error={errors.matricula?.message}>
              <input
                className="fasi-input"
                placeholder="202116040006"
                {...numericProps(12)}
                {...register('matricula')}
              />
            </Field>
            <Field label="CPF" required error={errors.cpf?.message}>
              <input
                className="fasi-input"
                placeholder="000.000.000-00"
                {...cpfProps()}
                {...register('cpf')}
              />
            </Field>
          </FieldGroup>

          <Field label="E-mail para envio" required error={errors.email?.message}>
            <input
              className="fasi-input"
              type="email"
              placeholder="seuemail@ufpa.br"
              {...register('email')}
            />
          </Field>
        </FormSection>

        <FormSection title="Documento solicitado">
          <Field label="Tipo de comprovante" required error={errors.tipo_documento?.message}>
            <select className="fasi-input" {...register('tipo_documento')}>
              <option value="">Selecione o tipo de documento</option>
              {TIPOS_DOCUMENTO.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </Field>
        </FormSection>

        <FormSection title="Histórico acadêmico">
          <div
            className="border-2 border-dashed border-border rounded-xl p-6 text-center
                       hover:border-fasi-400 hover:bg-fasi-50/30 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0] ?? null) }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={e => handleFile(e.target.files?.[0] ?? null)}
            />
            {historico ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="w-8 h-8 text-fasi-500" />
                <div className="text-left">
                  <p className="text-sm font-medium text-foreground">{historico.name}</p>
                  <p className="text-xs text-muted-foreground">{(historico.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <button
                  type="button"
                  onClick={e => { e.stopPropagation(); setHistorico(null) }}
                  className="ml-2 text-muted-foreground hover:text-red-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="text-muted-foreground">
                <Upload className="w-8 h-8 mx-auto mb-2 text-fasi-400" />
                <p className="text-sm font-medium">Clique ou arraste o PDF do histórico aqui</p>
                <p className="text-xs mt-1">Apenas PDF • máx. 50 MB</p>
              </div>
            )}
          </div>
          {!historico && mutation.isError && (
            <p className="text-xs text-red-500 mt-1">Histórico acadêmico é obrigatório.</p>
          )}
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Emitir e Enviar Documento" />
      </form>
    </PageShell>
  )
}
