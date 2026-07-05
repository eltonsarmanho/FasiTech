import { FieldErrors, UseFormRegister } from 'react-hook-form'

import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { FuncionarioNotFoundHint } from '@/shared/components/FuncionarioNotFoundHint'
import { MODALIDADES_TCC } from '@/shared/lib/constants'
import { numericProps } from '@/shared/lib/masks'
import { formatPeriodo, isPeriodoAtivo, type PeriodoSubmissao } from '@/shared/hooks/usePeriodosSubmissao'
import { type RequerimentoTccFormData } from './requerimentoTcc.shared'

interface RequerimentoTccFieldsProps {
  register: UseFormRegister<RequerimentoTccFormData>
  errors: FieldErrors<RequerimentoTccFormData>
  orientadores: string[]
  membrosBanca: string[]
  periodosDefesa: PeriodoSubmissao[]
  dataDefesaValue?: string
  showPeriodosInfo?: boolean
}

export function RequerimentoTccFields({
  register,
  errors,
  orientadores,
  membrosBanca,
  periodosDefesa,
  dataDefesaValue,
  showPeriodosInfo = true,
}: RequerimentoTccFieldsProps) {
  return (
    <>
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
        {showPeriodosInfo && periodosDefesa.length > 0 && (
          <div className="mb-4 text-sm rounded-lg border border-blue-200 bg-blue-50 p-3">
            <p className="font-semibold text-blue-700 mb-1">Períodos de defesa disponíveis:</p>
            <ul className="space-y-0.5 text-blue-600">
              {periodosDefesa.map(p => (
                <li key={p.id}>• Período {p.numero}: {formatPeriodo(p)}{p.semestre ? ` (${p.semestre})` : ''}</li>
              ))}
            </ul>
          </div>
        )}
        {showPeriodosInfo && periodosDefesa.length > 0 && dataDefesaValue && !isPeriodoAtivo(periodosDefesa, dataDefesaValue) && (
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
    </>
  )
}
