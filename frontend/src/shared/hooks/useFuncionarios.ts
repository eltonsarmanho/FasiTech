import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'

export interface FuncionarioPublico {
  nome: string
  titulo: string | null
  tipo: string | null        // 'Interno' | 'Externo'
  categoria: string | null   // 'Docente' | 'Secretaria' | 'Colaborador'
}

/**
 * Carrega a lista pública de funcionários (sem dados de contato) usada para
 * popular os seletores dos formulários. A filtragem por categoria/tipo é feita
 * no cliente para permitir combinações (ex.: Docente OU Colaborador).
 */
export function useFuncionarios() {
  return useQuery({
    queryKey: ['funcionarios-publico'],
    queryFn: async () => {
      const { data } = await api.get<{ funcionarios: FuncionarioPublico[] }>('/api/v1/funcionarios')
      return data.funcionarios
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })
}

/** Retorna apenas os nomes que satisfazem o predicado, em ordem alfabética. */
export function nomesFiltrados(
  funcionarios: FuncionarioPublico[],
  predicate: (f: FuncionarioPublico) => boolean,
): string[] {
  return funcionarios.filter(predicate).map(f => f.nome)
}
