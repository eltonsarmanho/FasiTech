import { FormCard } from '@/shared/components/FormCard'
import fasiLogo from '@/assets/fasiOficial.png'
import seloSebrae from '@/assets/selo-sebrae.png'

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
    icon: '📑',
    title: 'Componentes Curriculares Flexibilizados (CCF)',
    description: 'Registro de Componentes Curriculares Flexibilizados. Envie o PDF consolidado das atividades para análise.',
    to: '/ccf',
  },
  {
    icon: '📝',
    title: 'Requerimento de TCC',
    description: 'Registro dos dados para defesa do TCC com banca examinadora e informações adicionais.',
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
    description: 'Avalie a gestão da FASI. Feedback anônimo sobre transparência, comunicação e suporte.',
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

function SectionHeader({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="mb-5">
      <span className="fasi-section-eyebrow">{eyebrow}</span>
      <h2 className="fasi-section-title">{title}</h2>
    </div>
  )
}

export function HomePage() {
  return (
    <div className="animate-slide-up space-y-10">

      {/* ── Hero institucional ───────────────────────────────────────── */}
      <div className="fasi-header-gradient rounded-2xl overflow-hidden">
        <div className="flex flex-col md:flex-row items-center gap-6 px-8 md:px-12 py-10 md:py-12">
          <img
            src={fasiLogo}
            alt="FASI — Faculdade de Sistemas de Informação"
            className="h-20 md:h-24 object-contain bg-white rounded-xl px-4 py-2 shadow-navy-md shrink-0"
          />
          <div>
            <p
              className="text-[10px] font-bold tracking-[0.2em] uppercase mb-2"
              style={{ color: 'rgba(255,255,255,0.55)' }}
            >
              Universidade Federal do Pará · FASI
            </p>
            <h1 className="text-2xl md:text-3xl font-display font-bold text-white mb-2 leading-tight">
              Portal Acadêmico da FASI
            </h1>
            <p className="text-sm md:text-base leading-relaxed max-w-xl" style={{ color: 'rgba(255,255,255,0.75)' }}>
              Central integrada de serviços, formulários e documentos institucionais.
              Acesse todos os recursos acadêmicos de forma rápida e unificada.
            </p>
          </div>
        </div>
      </div>

      {/* ── Reconhecimento Sebrae ────────────────────────────────────── */}
      <div
        className="flex items-center gap-4 rounded-xl px-5 py-4"
        style={{ border: '1px solid #BBF7D0', background: '#F0FDF4' }}
      >
        <img
          src={seloSebrae}
          alt="Selo Sebrae — Prêmio Educador Transformador"
          className="h-28 w-28 shrink-0 object-contain"
        />
        <div>
          <p className="font-semibold text-sm" style={{ color: '#15803D' }}>
            2º Lugar na Gestão Educacional Transformadora · Prêmio Educador Transformador 3ª Edição
          </p>
          <p className="text-xs mt-1 leading-relaxed" style={{ color: '#16A34A' }}>
            O FasiTech foi reconhecido pelo Sebrae pela contribuição à inovação
            e digitalização dos processos acadêmicos da FASI/UFPA.
          </p>
        </div>
      </div>

      {/* ── Formulários para Discentes ──────────────────────────────── */}
      <section>
        <SectionHeader eyebrow="Discentes" title="Formulários para Alunos" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {studentForms.map(card => (
            <FormCard key={card.to} {...card} />
          ))}
        </div>
      </section>

      {/* ── Formulários para Docentes ───────────────────────────────── */}
      <section>
        <SectionHeader eyebrow="Docentes" title="Formulários para Professores" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {teacherForms.map(card => (
            <FormCard key={card.to} {...card} />
          ))}
        </div>
      </section>

      {/* ── Geral ───────────────────────────────────────────────────── */}
      <section>
        <SectionHeader eyebrow="Geral" title="Outros Serviços" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {generalItems.map(card => (
            <FormCard key={card.to} {...card} />
          ))}
        </div>
      </section>

      {/* ── Informações importantes ──────────────────────────────────── */}
      <div className="fasi-info-box">
        <p className="font-semibold mb-2" style={{ color: '#1e3a8a' }}>Informações Importantes</p>
        <ul className="space-y-1" style={{ color: '#1e40af' }}>
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
