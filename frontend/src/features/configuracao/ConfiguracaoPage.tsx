import { Link } from 'react-router-dom'
import { ClipboardList, FlaskConical, Bell, BookOpen, BarChart2, CalendarRange, Users, UserCheck } from 'lucide-react'

import { PageShell } from '@/shared/components/PageShell'
import { TokenGate } from '@/shared/components/TokenGate'

const items = [
  {
    icon: ClipboardList,
    title: 'Consulta Requerimento TCC',
    description: 'Visualização dos dados submetidos no Requerimento TCC — métricas e tabela.',
    to: '/consulta/requerimento-tcc',
    color: 'text-fasi-500',
  },
  {
    icon: FlaskConical,
    title: 'Consulta Projetos',
    description: 'Visualização e análise dos projetos submetidos pelos docentes.',
    to: '/consulta/projetos',
    color: 'text-fasi-500',
  },
  {
    icon: Bell,
    title: 'Gestor de Alertas',
    description: 'Criação de gatilhos de e-mail automáticos. Configure datas e horários de disparo.',
    to: '/admin/alertas',
    color: 'text-amber-500',
  },
  {
    icon: BookOpen,
    title: 'Lançamento de Conceitos',
    description: 'Painel para listar alunos por ACC, TCC e Estágio com filtros por turma, polo e período.',
    to: '/admin/lancamentos',
    color: 'text-amber-500',
  },
  {
    icon: BarChart2,
    title: 'Consulta dados da Gestão',
    description: 'Dashboard com insights quantitativos da avaliação da gestão FASI — médias, distribuições e uso do FasiTech.',
    to: '/consulta/gestao',
    color: 'text-fasi-500',
  },
  {
    icon: CalendarRange,
    title: 'Períodos de Submissão',
    description: 'Configure os períodos em que alunos podem enviar ACC, Estágio e Requerimento de TCC.',
    to: '/admin/periodos',
    color: 'text-amber-500',
  },
  {
    icon: Users,
    title: 'Gerenciamento de Funcionário',
    description: 'Cadastro de docentes e colaboradores — nome, titulação, tipo, contato e aniversário.',
    to: '/admin/funcionarios',
    color: 'text-amber-500',
  },
  {
    icon: UserCheck,
    title: 'Dashboard Social',
    description: 'Perfil socioeconômico dos discentes — gênero, renda, moradia, saúde mental, PCD e assistência estudantil.',
    to: '/consulta/social',
    color: 'text-fasi-500',
  },
]

export function ConfiguracaoPage() {
  return (
    <PageShell icon="⚙️" title="Configuração"
      subtitle="Acesso restrito — painéis administrativos da FASI">
      <TokenGate storageKey="fasi_config_auth">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {items.map(({ icon: Icon, title, description, to, color }) => (
            <Link
              key={to}
              to={to}
              className="fasi-card p-6 flex items-start gap-4 hover:shadow-fasi-md transition-shadow group"
            >
              <div className={`shrink-0 mt-0.5 ${color}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <p className="font-semibold text-foreground group-hover:text-fasi-600 transition-colors text-sm mb-1">
                  {title}
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
              </div>
            </Link>
          ))}
        </div>
      </TokenGate>
    </PageShell>
  )
}
