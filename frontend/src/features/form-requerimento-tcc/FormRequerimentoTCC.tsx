import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import toast from 'react-hot-toast'

import { PageShell } from '@/shared/components/PageShell'
import { SubmitButton } from '@/shared/components/SubmitButton'
import { submitJson, ApiError } from '@/shared/lib/api'
import { usePeriodosSubmissao, isPeriodoAtivo, formatPeriodo } from '@/shared/hooks/usePeriodosSubmissao'
import { useFuncionarios, nomesFiltrados } from '@/shared/hooks/useFuncionarios'
import {
  requerimentoTccSchema,
  type RequerimentoTccFormData,
  normalizeRequerimentoTccPayload,
} from './requerimentoTcc.shared'
import { RequerimentoTccFields } from './RequerimentoTccFields'

export function FormRequerimentoTCC() {
  const { data: periodosDefesa = [] } = usePeriodosSubmissao('tcc')
  const { data: funcionarios = [] } = useFuncionarios()
  // Orientador: somente docentes internos. Banca: docentes internos e externos.
  const orientadores = nomesFiltrados(funcionarios, f => f.categoria === 'Docente' && f.tipo === 'Interno')
  const membrosBanca = nomesFiltrados(funcionarios, f => f.categoria === 'Docente')

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<RequerimentoTccFormData>({
    resolver: zodResolver(requerimentoTccSchema),
  })

  const dataDefesaValue = watch('data_defesa')
  const [conflictErrors, setConflictErrors] = useState<string[]>([])

  const mutation = useMutation({
    mutationFn: (data: RequerimentoTccFormData) => {
      // Validação de período no frontend (dupla validação com backend)
      if (periodosDefesa.length > 0 && data.data_defesa && !isPeriodoAtivo(periodosDefesa, data.data_defesa)) {
        const detalhes = periodosDefesa.map(p => `Período ${p.numero}: ${formatPeriodo(p)}`).join(' | ')
        throw new Error(`A data de defesa está fora dos períodos permitidos. Períodos: ${detalhes}`)
      }
      const payload = normalizeRequerimentoTccPayload(data)
      return submitJson('/api/v1/forms/requerimento-tcc', payload)
    },
    onSuccess: () => {
      setConflictErrors([])
      toast.success('Requerimento de TCC registrado com sucesso!')
      reset()
    },
    onError: (e: Error) => {
      setConflictErrors([])
      if (e instanceof ApiError) {
        const detail = e.detail as { type?: string; conflitos?: string[] } | null
        if (detail?.type === 'cruzamento_horario' && Array.isArray(detail.conflitos)) {
          setConflictErrors(detail.conflitos)
          return
        }
      }
      toast.error(e.message || 'Erro ao registrar. Tente novamente.')
    },
  })

  return (
    <PageShell icon="📝" title="Requerimento de TCC"
      subtitle="Registro de informações para defesa do Trabalho de Conclusão de Curso">

      <div className="fasi-info-box mb-6">
        <strong>Importante:</strong> Todos os campos são obrigatórios, exceto o Membro 3 da Banca. Para TCC em dupla, ambos os alunos devem registrar as mesmas informações.
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
        <RequerimentoTccFields
          register={register}
          errors={errors}
          orientadores={orientadores}
          membrosBanca={membrosBanca}
          periodosDefesa={periodosDefesa}
          dataDefesaValue={dataDefesaValue}
        />

        <SubmitButton loading={mutation.isPending} label="Enviar Requerimento" />

        {conflictErrors.length > 0 && (
          <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4">
            <p className="flex items-center gap-2 font-semibold text-red-700 mb-2">
              <span>⚠️</span> Conflito de horário detectado
            </p>
            <ul className="space-y-1.5 text-sm text-red-700">
              {conflictErrors.map((msg, i) => (
                <li key={i} className="flex gap-2">
                  <span className="mt-0.5 shrink-0">•</span>
                  <span>{msg}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-red-600">
              Ajuste a data e/ou horário da defesa para evitar o conflito antes de enviar novamente.
            </p>
          </div>
        )}
      </form>
    </PageShell>
  )
}
