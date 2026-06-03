import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useState } from 'react'

import { PageShell } from '@/shared/components/PageShell'
import { FormSection, Field } from '@/shared/components/FormSection'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { submitJson } from '@/shared/lib/api'

const SATISFACAO = [
  'Muito insatisfeito',
  'Insatisfeito',
  'Neutro',
  'Satisfeito',
  'Muito satisfeito',
] as const

const CONCORDANCIA = [
  'Discordo totalmente',
  'Discordo',
  'Neutro',
  'Concordo',
  'Concordo totalmente',
] as const

const QUESTIONS = [
  { key: 'q1_transparencia',   escala: SATISFACAO,   label: '1. Como você avalia a transparência da gestão da Faculdade de Sistemas de Informação?' },
  { key: 'q2_comunicacao',     escala: SATISFACAO,   label: '2. Como você avalia a comunicação entre a gestão e os alunos/professores?' },
  { key: 'q3_acessibilidade',  escala: SATISFACAO,   label: '3. Como você avalia a acessibilidade da gestão para tratar de questões e preocupações?' },
  { key: 'q4_inclusao',        escala: CONCORDANCIA, label: '4. A gestão da faculdade promove um ambiente acadêmico inclusivo e diversificado?' },
  { key: 'q5_planejamento',    escala: SATISFACAO,   label: '5. Como você avalia o planejamento das atividades acadêmicas, incluindo a oferta de disciplinas e a alocação de professores?' },
  { key: 'q6_recursos',        escala: SATISFACAO,   label: '6. Como você avalia a gestão de recursos (infraestrutura, tecnologia, materiais) pela administração da faculdade?' },
  { key: 'q7_eficiencia',      escala: CONCORDANCIA, label: '7. A gestão da faculdade é eficiente em resolver problemas administrativos e operacionais?' },
  { key: 'q8_suporte',         escala: SATISFACAO,   label: '8. Como você avalia o suporte acadêmico fornecido pela gestão, incluindo orientação acadêmica e apoio ao aluno?' },
  { key: 'q9_extracurricular', escala: CONCORDANCIA, label: '9. A gestão da faculdade promove atividades extracurriculares e de desenvolvimento profissional que atendem às necessidades dos alunos?' },
] as const

const FASITECH_IMPACTO: readonly string[] = [
  'Discordo totalmente',
  'Discordo',
  'Neutro',
  'Concordo',
  'Concordo totalmente',
]

const FASITECH_FUNCIONALIDADES = [
  'Formulário de ACC',
  'Formulário de TCC',
  'Formulário de Estágio',
  'Requerimento de TCC',
  'Emissão de Documentos',
  'Formulário Social',
  'FAQ / Assistente IA (Diretor Virtual)',
  'Nenhuma',
] as const

function RadioGroup({ name, options, register }: {
  name: string
  options: readonly string[]
  register: ReturnType<typeof useForm>['register']
}) {
  return (
    <div className="flex flex-col sm:flex-row flex-wrap gap-2 mt-2">
      {options.map(opt => (
        <label key={opt} className="flex items-center gap-1.5 cursor-pointer">
          <input type="radio" value={opt} className="accent-fasi-500" {...register(name)} />
          <span className="text-sm text-muted-foreground">{opt}</span>
        </label>
      ))}
    </div>
  )
}

export function FormAvaliacao() {
  const { register, handleSubmit, reset } = useForm()
  const [funcionalidades, setFuncionalidades] = useState<string[]>([])

  function toggleFuncionalidade(opt: string) {
    setFuncionalidades(prev =>
      prev.includes(opt) ? prev.filter(v => v !== opt) : [...prev, opt]
    )
  }

  const mutation = useMutation({
    mutationFn: (data: object) =>
      submitJson('/api/v1/forms/avaliacao-gestao', {
        ...data,
        q13_fasitech_funcionalidades: funcionalidades,
      }),
    onSuccess: () => {
      toast.success('Avaliação registrada! Obrigado pelo feedback.')
      reset()
      setFuncionalidades([])
    },
    onError: () => toast.error('Erro ao registrar.'),
  })

  return (
    <PageShell icon="📊" title="Avaliação da Gestão FASI"
      subtitle="Feedback anônimo sobre transparência, comunicação e suporte institucional">

      <div className="fasi-info-box mb-6">
        🔒 <strong>Todas as respostas são anônimas.</strong> Nenhuma informação pessoal será coletada ou vinculada às suas respostas.
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <FormSection title="📋 Seção 1: Avaliação Geral da Gestão">
          <div className="space-y-6">
            {QUESTIONS.slice(0, 4).map(({ key, label, escala }) => (
              <Field key={key} label={label}>
                <RadioGroup name={key} options={escala} register={register} />
              </Field>
            ))}
          </div>
        </FormSection>

        <FormSection title="📅 Seção 2: Planejamento e Organização">
          <div className="space-y-6">
            {QUESTIONS.slice(4, 7).map(({ key, label, escala }) => (
              <Field key={key} label={label}>
                <RadioGroup name={key} options={escala} register={register} />
              </Field>
            ))}
          </div>
        </FormSection>

        <FormSection title="🎓 Seção 3: Suporte Acadêmico e Estudantil">
          <div className="space-y-6">
            {QUESTIONS.slice(7).map(({ key, label, escala }) => (
              <Field key={key} label={label}>
                <RadioGroup name={key} options={escala} register={register} />
              </Field>
            ))}
          </div>
        </FormSection>

        <FormSection title="💬 Seção 4: Sugestões e Comentários">
          <div className="space-y-4">
            <Field label="10. Que melhorias você sugeriria para a gestão da faculdade?">
              <textarea
                className="fasi-input min-h-[120px]"
                placeholder="Digite suas sugestões de melhoria aqui..."
                {...register('q10_melhorias')}
              />
            </Field>
            <Field label="11. Existem outras questões que você gostaria de destacar em relação à gestão da Faculdade de Sistemas de Informação?">
              <textarea
                className="fasi-input min-h-[100px]"
                placeholder="Digite outros comentários ou observações aqui..."
                {...register('q11_outras_questoes')}
              />
            </Field>
          </div>
        </FormSection>

        <FormSection title="🖥️ Seção 5: FasiTech — Portal Acadêmico">
          <div className="space-y-6">
            <Field label="12. O FasiTech facilitou o envio e acompanhamento dos seus processos acadêmicos (ACC, TCC, Estágio etc.)?">
              <RadioGroup name="q12_fasitech_impacto" options={FASITECH_IMPACTO} register={register} />
            </Field>
            <Field label="13. Quais funcionalidades do FasiTech você já utilizou? (Selecione todas que se aplicam)">
              <div className="flex flex-col sm:flex-row flex-wrap gap-2 mt-2">
                {FASITECH_FUNCIONALIDADES.map(opt => (
                  <label key={opt} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      className="accent-fasi-500"
                      checked={funcionalidades.includes(opt)}
                      onChange={() => toggleFuncionalidade(opt)}
                    />
                    <span className="text-sm text-muted-foreground">{opt}</span>
                  </label>
                ))}
              </div>
            </Field>
          </div>
        </FormSection>

        <SubmitButton loading={mutation.isPending} label="Enviar Avaliação" />
      </form>
    </PageShell>
  )
}
