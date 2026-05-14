import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'

export function usePeriodosLetivos() {
  return useQuery({
    queryKey: ['periodos-letivos'],
    queryFn: async () => {
      const { data } = await api.get<{ periodos: string[] }>('/api/v1/config/periodos-letivos')
      return data.periodos
    },
    staleTime: Infinity,
    gcTime: Infinity,
  })
}
