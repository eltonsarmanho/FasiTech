import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'

export interface PeriodoSubmissao {
  id: number
  tipo: string
  numero: number
  data_inicio: string
  data_fim: string
  semestre: string | null
}

export function usePeriodosSubmissao(tipo: 'tcc' | 'acc' | 'estagio' | 'ccf') {
  return useQuery({
    queryKey: ['periodos-submissao', tipo],
    queryFn: async () => {
      const { data } = await api.get<{ periodos: PeriodoSubmissao[] }>(
        `/api/v1/config/periodos-submissao?tipo=${tipo}`
      )
      return data.periodos
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function isPeriodoAtivo(periodos: PeriodoSubmissao[], date: string): boolean {
  return periodos.some(p => p.data_inicio <= date && date <= p.data_fim)
}

export function formatPeriodo(p: PeriodoSubmissao): string {
  const inicio = new Date(p.data_inicio + 'T12:00:00').toLocaleDateString('pt-BR')
  const fim = new Date(p.data_fim + 'T12:00:00').toLocaleDateString('pt-BR')
  return `${inicio} até ${fim}`
}
