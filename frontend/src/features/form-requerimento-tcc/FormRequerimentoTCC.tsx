import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { MODALIDADES_TCC } from '@/shared/lib/constants'
import { submitJson } from '@/shared/lib/api'
import { numericProps, MATRICULA_REGEX, MATRICULA_MSG, ANO_REGEX, ANO_MSG, EMAIL_MSG } from '@/shared/lib/masks'
import { usePeriodosSubmissao, isPeriodoAtivo, formatPeriodo } from '@/shared/hooks/usePeriodosSubmissao'
import { useFuncionarios, nomesFiltrados } from '@/shared/hooks/useFuncionarios'
import { FuncionarioNotFoundHint } from '@/shared/components/FuncionarioNotFoundHint'

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
  membro_banca2:    z.string().min(1, 'Membro 2 obrigatório'),
  membro_banca3:    z.string().optional(),
  data_defesa:      z.string().min(1, 'Data de defesa obrigatória'),
  horario_defesa:   z.string().regex(/^\d{1,2}:\d{2}$/, 'Use o formato HH:MM (ex: 14:30)'),
  local_defesa:     z.string().optional(),
})
type FormData = z.infer<typeof schema>

export function FormRequerimentoTCC() {
  const { data: periodosDefesa = [] } = usePeriodosSubmissao('tcc')
  const { data: funcionarios = [] } = useFuncionarios()
  // Orientador: somente docentes internos. Banca: docentes internos e externos.
  const orientadores = nomesFiltrados(funcionarios, f => f.categoria === 'Docente' && f.tipo === 'Interno')
  const membrosBanca = nomesFiltrados(funcionarios, f => f.categoria === 'Docente')

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const dataDefesaValue = watch('data_defesa')

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      // Validação de período no frontend (dupla validação com backend)
      if (periodosDefesa.length > 0 && data.data_defesa && !isPeriodoAtivo(periodosDefesa, data.data_defesa)) {
        const detalhes = periodosDefesa.map(p => `Período ${p.numero}: ${formatPeriodo(p)}`).join(' | ')
        throw new Error(`A data de defesa está fora dos períodos permitidos. Períodos: ${detalhes}`)
      }
      const payload = {
        ...data,
        membro_banca3: data.membro_banca3 === 'Nenhum' || !data.membro_banca3 ? '' : data.membro_banca3,
      }
      return submitJson('/api/v1/forms/requerimento-tcc', payload)
    },
    onSuccess: () => { toast.success('Requerimento de TCC registrado com sucesso!'); reset() },
    onError: (e: Error) => toast.error(e.message || 'Erro ao registrar. Tente novamente.'),
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
                {orientadores.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <FuncionarioNotFoundHint />
            </Field>
            <Field label="Coorientador(a)">
              <input className="fasi-input" placeholder="Nome do coorientador (opcional)" {...register('coorientador')} />
            </Field>
          </FieldGroup>

          <FieldGroup cols={1}>
            <Field label="Membro 1 da Banca" required error={errors.membro_banca1?.message}>
              <select className="fasi-input" {...register('membro_banca1')}>
                <option value="">Selecione o membro 1...</option>
                {membrosBanca.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>

            <Field label="Membro 2 da Banca" required error={errors.membro_banca2?.message}>
              <select className="fasi-input" {...register('membro_banca2')}>
                <option value="">Selecione o membro 2...</option>
                {membrosBanca.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>

            <Field label="Membro 3 da Banca (opcional)">
              <select className="fasi-input" {...register('membro_banca3')}>
                <option value="Nenhum">Nenhum</option>
                {membrosBanca.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <FuncionarioNotFoundHint />
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
          {periodosDefesa.length > 0 && (
            <div className="mb-4 text-sm rounded-lg border border-blue-200 bg-blue-50 p-3">
              <p className="font-semibold text-blue-700 mb-1">Períodos de defesa disponíveis:</p>
              <ul className="space-y-0.5 text-blue-600">
                {periodosDefesa.map(p => (
                  <li key={p.id}>• Período {p.numero}: {formatPeriodo(p)}{p.semestre ? ` (${p.semestre})` : ''}</li>
                ))}
              </ul>
            </div>
          )}
          {periodosDefesa.length > 0 && dataDefesaValue && !isPeriodoAtivo(periodosDefesa, dataDefesaValue) && (
            <div className="mb-4 text-sm rounded-lg border border-red-200 bg-red-50 p-3 text-red-700">
              A data selecionada está fora dos períodos de defesa permitidos.
            </div>
          )}
          <FieldGroup cols={3}>
            <Field label="Data da defesa" required error={errors.data_defesa?.message}>
              <input className="fasi-input" type="date" {...register('data_defesa')} />
            </Field>
            <Field label="Horário" required error={errors.horario_defesa?.message}>
              <input
                className="fasi-input"
                type="text"
                placeholder="Ex: 14:30"
                maxLength={5}
                {...register('horario_defesa')}
              />
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
