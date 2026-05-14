import { FormCard } from '@/shared/components/FormCard'
import fasiLogo from '@/assets/fasiOficial.png'

// ── Dados dos cards ──────────────────────────────────────────────────────────

const studentForms = [
  {
    icon: '🎓',
    title: 'Formulário de ACC',
    description: 'Submissão de Atividades Complementares Curriculares. Envie seus certificados em PDF para análise.',
    to: '/acc',
  },
  {
    icon: '📚',
    title: 'Formulário TCC',
    description: 'Submissão do Trabalho de Conclusão de Curso (TCC 1 e TCC 2). Envie os documentos obrigatórios.',
    to: '/tcc',
  },
  {
    icon: '📋',
    title: 'Formulário de Estágio',
    description: 'Envio de documentos de Estágio I e II. Plano de Estágio ou Relatório Final.',
    to: '/estagio',
  },
  {
    icon: '📝',
    title: 'Requerimento de TCC',
    description: 'Registro dos dados para defesa do TCC — banca examinadora e informações adicionais.',
    to: '/requerimento-tcc',
  },
  {
    icon: '🤝',
    title: 'Formulário Social',
    description: 'Perfil socioeconômico, inclusão, diversidade e saúde mental. Dados para políticas institucionais.',
    to: '/social',
  },
  {
    icon: '📊',
    title: 'Avaliação da Gestão',
    description: 'Avalie a gestão da FASI — feedback anônimo sobre transparência, comunicação e suporte.',
    to: '/avaliacao-gestao',
  },
]

const teacherForms = [
  {
    icon: '📖',
    title: 'Plano de Ensino',
    description: 'Submissão de Planos de Ensino por disciplina, organizados por semestre letivo.',
    to: '/plano-ensino',
  },
  {
    icon: '🔬',
    title: 'Projetos',
    description: 'Registro de Projetos de Ensino, Pesquisa e Extensão. Novos, renovações ou encerramentos.',
    to: '/projetos',
  },
]

const generalItems = [
  {
    icon: '📄',
    title: 'Emissão de Documentos',
    description: 'Solicite comprovante de conclusão de curso ou comprovante de matrícula ativa.',
    to: '/emissao-documentos',
  },
  {
    icon: '📊',
    title: 'Dados Sociais',
    description: 'Download dos dados sociais dos discentes para pesquisa. Anonimizados conforme LGPD.',
    to: '/api/v1/dados-sociais/download',
    external: true,
  },
]

// ── Componente ───────────────────────────────────────────────────────────────

export function HomePage() {
  return (
    <div className="animate-slide-up space-y-10">
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className="fasi-header-gradient rounded-2xl p-8 md:p-12 text-white relative overflow-hidden">
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-white/5 pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-40 h-40 rounded-full bg-white/5 pointer-events-none" />

        <div className="relative flex flex-col md:flex-row items-center gap-6">
          <img
            src={fasiLogo}
            alt="FASI — Faculdade de Sistemas de Informação"
            className="h-20 md:h-24 object-contain bg-white rounded-xl px-4 py-2 shadow-fasi-md"
          />
          <div>
            <h1 className="text-2xl md:text-3xl font-bold mb-2">
              Portal Acadêmico da FASI
            </h1>
            <p className="text-white/80 text-sm md:text-base leading-relaxed max-w-xl">
              Central integrada de serviços, formulários e documentos institucionais.
              Acesse todos os recursos acadêmicos de forma rápida e unificada.
            </p>
          </div>
        </div>
      </div>

      {/* ── Formulários Discentes ─────────────────────────────────────────── */}
      <section>
        <h2 className="fasi-section-title">🎓 Formulários para Discentes</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {studentForms.map(card => (
            <FormCard key={card.to} {...card} />
          ))}
        </div>
      </section>

      {/* ── Formulários Docentes ──────────────────────────────────────────── */}
      <section>
        <h2 className="fasi-section-title">👨‍🏫 Formulários para Docentes</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {teacherForms.map(card => (
            <FormCard key={card.to} {...card} />
          ))}
        </div>
      </section>

      {/* ── Geral ────────────────────────────────────────────────────────── */}
      <section>
        <h2 className="fasi-section-title">🌐 Geral</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {generalItems.map(card => (
            <FormCard key={card.to} {...card} />
          ))}
        </div>
      </section>

      {/* ── Info box ────────────────────────────────────────────────────── */}
      <div className="fasi-info-box">
        <p className="font-semibold text-fasi-700 mb-2">ℹ️ Informações Importantes</p>
        <ul className="space-y-1 text-fasi-800">
          <li>• Todos os formulários exigem dados pessoais e documentos em formato PDF</li>
          <li>• Certifique-se que sua matrícula está ativa no SIGAA antes de enviar</li>
          <li>• Você receberá confirmação por e-mail após o processamento</li>
          <li>• Documentos armazenados de forma segura no Google Drive institucional</li>
          <li>• Dúvidas: <a href="mailto:fasicuntins@ufpa.br" className="underline font-medium">fasicuntins@ufpa.br</a></li>
        </ul>
      </div>
    </div>
  )
}
