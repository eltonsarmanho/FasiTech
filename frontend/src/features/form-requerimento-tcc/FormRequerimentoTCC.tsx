import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { PROFESSORES, MODALIDADES_TCC } from '@/shared/lib/constants'
import { submitJson } from '@/shared/lib/api'
import { numericProps, MATRICULA_REGEX, MATRICULA_MSG, ANO_REGEX, ANO_MSG, EMAIL_MSG } from '@/shared/lib/masks'

const MEMBROS_BANCA = [...PROFESSORES, 'Outro'] as const

const schema = z.object({
  nome_aluno:       z.string().min(3, 'Nome obrigatório'),
  matricula:        z.string().regex(MATRICULA_REGEX, MATRICULA_MSG),
  email:            z.string().email(EMAIL_MSG),
  telefone:         z.string().optional(),
  turma:            z.string().regex(ANO_REGEX, ANO_MSG),
  orientador:       z.string().min(1, 'Orientador obrigatório'),
  coorientador:     z.string().optional(),
  titulo_trabalho:  z.string().min(3, 'Título obrigatório'),
  resumo:           z.string().min(10, 'Resumo obrigatório'),
  palavra_chave:    z.string().min(1, 'Palavras-chave obrigatórias'),
  modalidade:       z.string().min(1, 'Modalidade obrigatória'),
  membro_banca1:    z.string().min(1, 'Membro 1 obrigatório'),
  membro_banca1_outro: z.string().optional(),
  membro_banca2:    z.string().min(1, 'Membro 2 obrigatório'),
  membro_banca2_outro: z.string().optional(),
  membro_banca3:    z.string().optional(),
  membro_banca3_outro: z.string().optional(),
  data_defesa:      z.string().min(1, 'Data de defesa obrigatória'),
  horario_defesa:   z.string().optional(),
  local_defesa:     z.string().optional(),
})
type FormData = z.infer<typeof schema>

export function FormRequerimentoTCC() {
  const [membro1, setMembro1] = useState('')
  const [membro2, setMembro2] = useState('')
  const [membro3, setMembro3] = useState('')

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const payload = {
        ...data,
        membro_banca1: data.membro_banca1 === 'Outro' ? (data.membro_banca1_outro ?? '') : data.membro_banca1,
        membro_banca2: data.membro_banca2 === 'Outro' ? (data.membro_banca2_outro ?? '') : data.membro_banca2,
        membro_banca3: data.membro_banca3 === 'Nenhum' || !data.membro_banca3 ? '' :
          data.membro_banca3 === 'Outro' ? (data.membro_banca3_outro ?? '') : data.membro_banca3,
      }
      return submitJson('/api/v1/forms/requerimento-tcc', payload)
    },
    onSuccess: () => { toast.success('Requerimento de TCC registrado com sucesso!'); reset(); setMembro1(''); setMembro2(''); setMembro3('') },
    onError: () => toast.error('Erro ao registrar. Tente novamente.'),
  })

  return (
    <PageShell icon="📝" title="Requerimento de TCC"
      subtitle="Registro de informações para defesa do Trabalho de Conclusão de Curso">

      <div className="fasi-info-box mb-6">
        <strong>Importante:</strong> Todos os campos são obrigatórios, exceto o Membro 3 da Banca. Para TCC em dupla, ambos os alunos devem registrar as mesmas informações.
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="Dados do Discente">
          <FieldGroup cols={2}>
            <Field label="Nome completo" required error={errors.nome_aluno?.message}>
              <input className="fasi-input" placeholder="Seu nome completo" {...register('nome_aluno')} />
            </Field>
            <Field label="Matrícula" required error={errors.matricula?.message}>
              <input className="fasi-input" placeholder="202116040006" {...numericProps(12)} {...register('matricula')} />
            </Field>
            <Field label="E-mail" required error={errors.email?.message}>
              <input className="fasi-input" type="email" placeholder="seuemail@ufpa.br" {...register('email')} />
            </Field>
            <Field label="Telefone / WhatsApp">
              <input className="fasi-input" placeholder="(91) 99999-9999" {...register('telefone')} />
            </Field>
            <Field label="Ano de ingresso (Turma)" required error={errors.turma?.message}>
              <input className="fasi-input" placeholder="2026" {...numericProps(4)} {...register('turma')} />
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Banca Examinadora">
          <FieldGroup cols={1}>
            <Field label="Orientador(a)" required error={errors.orientador?.message}>
              <select className="fasi-input" {...register('orientador')}>
                <option value="">Selecione o orientador...</option>
                {PROFESSORES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Coorientador(a)">
              <input className="fasi-input" placeholder="Nome do coorientador (opcional)" {...register('coorientador')} />
            </Field>
          </FieldGroup>

          <FieldGroup cols={1}>
            <Field label="Membro 1 da Banca" required error={errors.membro_banca1?.message}>
              <select className="fasi-input" {...register('membro_banca1')} onChange={e => setMembro1(e.target.value)}>
                <option value="">Selecione o membro 1...</option>
                {MEMBROS_BANCA.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            {membro1 === 'Outro' && (
              <Field label="Nome do Membro 1 (especifique)" required>
                <input className="fasi-input" placeholder="Nome completo do membro externo" {...register('membro_banca1_outro')} />
              </Field>
            )}

            <Field label="Membro 2 da Banca" required error={errors.membro_banca2?.message}>
              <select className="fasi-input" {...register('membro_banca2')} onChange={e => setMembro2(e.target.value)}>
                <option value="">Selecione o membro 2...</option>
                {MEMBROS_BANCA.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            {membro2 === 'Outro' && (
              <Field label="Nome do Membro 2 (especifique)" required>
                <input className="fasi-input" placeholder="Nome completo do membro externo" {...register('membro_banca2_outro')} />
              </Field>
            )}

            <Field label="Membro 3 da Banca (opcional)">
              <select className="fasi-input" {...register('membro_banca3')} onChange={e => setMembro3(e.target.value)}>
                <option value="Nenhum">Nenhum</option>
                {MEMBROS_BANCA.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            {membro3 === 'Outro' && (
              <Field label="Nome do Membro 3 (especifique)">
                <input className="fasi-input" placeholder="Nome completo do membro externo" {...register('membro_banca3_outro')} />
              </Field>
            )}
          </FieldGroup>
        </FormSection>

        <FormSection title="Informações do Trabalho">
          <FieldGroup cols={1}>
            <Field label="Título do trabalho" required error={errors.titulo_trabalho?.message}
              hint="Para TCC em dupla, ambos devem registrar o mesmo título.">
              <input className="fasi-input" placeholder="Título completo do trabalho" {...register('titulo_trabalho')} />
            </Field>
            <Field label="Resumo" required error={errors.resumo?.message}
              hint="Para TCC em dupla, ambos devem registrar o mesmo resumo.">
              <textarea className="fasi-input min-h-[120px]" placeholder="Resumo do trabalho..." {...register('resumo')} />
            </Field>
            <Field label="Palavras-chave" required error={errors.palavra_chave?.message}
              hint="Para TCC em dupla, ambos devem registrar as mesmas palavras-chave.">
              <input className="fasi-input" placeholder="Palavra1, Palavra2, Palavra3" {...register('palavra_chave')} />
            </Field>
          </FieldGroup>

          <Field label="Modalidade do trabalho" required error={errors.modalidade?.message}>
            <select className="fasi-input" {...register('modalidade')}>
              <option value="">Selecione uma opção...</option>
              {MODALIDADES_TCC.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </Field>
        </FormSection>

        <FormSection title="Data e Local da Defesa">
          <FieldGroup cols={3}>
            <Field label="Data da defesa" required error={errors.data_defesa?.message}>
              <input className="fasi-input" type="date" {...register('data_defesa')} />
            </Field>
            <Field label="Horário">
              <input className="fasi-input" type="time" {...register('horario_defesa')} />
            </Field>
            <Field label="Local">
              <input className="fasi-input" placeholder="Ex.: Sala 101, Campus Cametá" {...register('local_defesa')} />
            </Field>
          </FieldGroup>
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar Requerimento" />
      </form>
    </PageShell>
  )
}
