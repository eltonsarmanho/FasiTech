import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, FieldGroup, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { POLOS, GENEROS, COR_ETNIA_OPTIONS, RENDA_OPTIONS } from '@/shared/lib/constants'
import { usePeriodosLetivos } from '@/shared/hooks/usePeriodosLetivos'
import { submitJson } from '@/shared/lib/api'
import { numericProps } from '@/shared/lib/masks'

const SIM_NAO = ['Sim', 'Não'] as const
const MORADIA = ['Própria', 'Alugada', 'Cedida', 'Quilombola/Indígena', 'Outro'] as const
const TRABALHO_OPT = ['Não trabalho', 'Trabalho com carteira assinada', 'Autônomo/Informal', 'Estágio', 'Outro'] as const
const DESLOCAMENTO = ['A pé', 'Bicicleta', 'Moto', 'Carro próprio', 'Transporte público', 'Barco/Fluvial', 'Outro'] as const
const ASSIST_EST = ['Não recebo', 'Ótima', 'Boa', 'Regular', 'Ruim', 'Péssima'] as const
const SAUDE_MENTAL = ['Ótima', 'Boa', 'Regular', 'Ruim', 'Péssima'] as const
const ESCOLARIDADE = ['Sem escolaridade', 'Fundamental incompleto', 'Fundamental completo', 'Médio incompleto', 'Médio completo', 'Superior incompleto', 'Superior completo', 'Pós-graduação'] as const
const ACESSO_INTERNET = ['Muito ruim', 'Ruim', 'Regular', 'Boa', 'Muito boa'] as const

export function FormSocial() {
  const { data: periodos = [] } = usePeriodosLetivos()
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm()
  const pcd = watch('pcd')

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => submitJson('/api/v1/forms/social', data),
    onSuccess: () => { toast.success('Formulário social enviado! Obrigado pela participação.'); reset() },
    onError: () => toast.error('Erro ao enviar. Tente novamente.'),
  })

  return (
    <PageShell icon="🤝" title="Formulário Social"
      subtitle="Perfil socioeconômico, diversidade e saúde mental — dados para políticas institucionais">
      <div className="fasi-info-box mb-6">
        Suas respostas são <strong>confidenciais</strong> e usadas apenas para fins de pesquisa institucional.
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d as Record<string, unknown>))} noValidate>
        <FormSection title="Identificação">
          <FieldGroup cols={2}>
            <Field label="Matrícula" required error={(errors.matricula?.message) as string | undefined}>
              <input
                className="fasi-input"
                placeholder="202116040006"
                {...numericProps(12)}
                {...register('matricula', {
                  required: 'Matrícula obrigatória',
                  pattern: { value: /^\d{12}$/, message: 'Matrícula deve ter exatamente 12 dígitos numéricos' },
                })}
              />
            </Field>
            <Field label="Período de referência" required>
              <select className="fasi-input" {...register('periodo_referencia', { required: true })}>
                <option value="">Selecione</option>
                {periodos.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Gênero">
              <select className="fasi-input" {...register('genero')}>
                <option value="">Selecione</option>
                {GENEROS.map(g => <option key={g}>{g}</option>)}
              </select>
            </Field>
            <Field label="Polo">
              <select className="fasi-input" {...register('polo')}>
                <option value="">Selecione</option>
                {POLOS.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Dados Demográficos">
          <FieldGroup cols={2}>
            <Field label="Cor/Etnia">
              <select className="fasi-input" {...register('cor_etnia')}>
                <option value="">Selecione</option>
                {COR_ETNIA_OPTIONS.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Pessoa com Deficiência (PCD)?">
              <select className="fasi-input" {...register('pcd')}>
                <option value="">Selecione</option>
                {SIM_NAO.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            {pcd === 'Sim' && (
              <Field label="Tipo de deficiência" className="sm:col-span-2">
                <input className="fasi-input" placeholder="Descreva o tipo de deficiência" {...register('tipo_deficiencia')} />
              </Field>
            )}
          </FieldGroup>
        </FormSection>

        <FormSection title="Dados Socioeconômicos">
          <FieldGroup cols={2}>
            <Field label="Renda familiar">
              <select className="fasi-input" {...register('renda')}>
                <option value="">Selecione</option>
                {RENDA_OPTIONS.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Situação de trabalho">
              <select className="fasi-input" {...register('trabalho')}>
                <option value="">Selecione</option>
                {TRABALHO_OPT.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Principal meio de deslocamento">
              <select className="fasi-input" {...register('deslocamento')}>
                <option value="">Selecione</option>
                {DESLOCAMENTO.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Tipo de moradia">
              <select className="fasi-input" {...register('tipo_moradia')}>
                <option value="">Selecione</option>
                {MORADIA.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Assistência estudantil">
              <select className="fasi-input" {...register('assistencia_estudantil')}>
                <option value="">Selecione</option>
                {ASSIST_EST.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Saúde Mental">
          <FieldGroup cols={2}>
            <Field label="Como avalia sua saúde mental atualmente?">
              <select className="fasi-input" {...register('saude_mental')}>
                <option value="">Selecione</option>
                {SAUDE_MENTAL.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Nível de estresse relacionado ao curso">
              <select className="fasi-input" {...register('estresse')}>
                <option value="">Selecione</option>
                {SAUDE_MENTAL.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Possui acompanhamento psicológico/psiquiátrico?" className="sm:col-span-2">
              <input className="fasi-input" placeholder="Ex.: Sim, pelo CAPS. Não." {...register('acompanhamento')} />
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Escolaridade dos Responsáveis">
          <FieldGroup cols={2}>
            <Field label="Escolaridade do pai">
              <select className="fasi-input" {...register('escolaridade_pai')}>
                <option value="">Selecione</option>
                {ESCOLARIDADE.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Escolaridade da mãe">
              <select className="fasi-input" {...register('escolaridade_mae')}>
                <option value="">Selecione</option>
                {ESCOLARIDADE.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
          </FieldGroup>
        </FormSection>

        <FormSection title="Recursos Tecnológicos">
          <FieldGroup cols={2}>
            <Field label="Qtd. de computadores em casa">
              <input className="fasi-input" type="number" min="0" {...register('qtd_computador')} />
            </Field>
            <Field label="Qtd. de celulares em casa">
              <input className="fasi-input" type="number" min="0" {...register('qtd_celular')} />
            </Field>
            <Field label="Possui computador próprio?">
              <select className="fasi-input" {...register('computador_proprio')}>
                <option value="">Selecione</option>
                {SIM_NAO.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Qualidade do acesso à internet em casa">
              <select className="fasi-input" {...register('acesso_internet')}>
                <option value="">Selecione</option>
                {ACESSO_INTERNET.map(o => <option key={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Gasto mensal com internet">
              <input className="fasi-input" placeholder="Ex.: R$ 80,00 / mês" {...register('gasto_internet')} />
            </Field>
          </FieldGroup>
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar Formulário Social" />
      </form>
    </PageShell>
  )
}
