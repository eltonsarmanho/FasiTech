import { PageShell } from '@/shared/components/PageShell'

const calendarios = [
  {
    label: 'Planilha de Ofertas por Período',
    description: 'Grade de disciplinas ofertadas organizadas por semestre letivo.',
    url: 'https://docs.google.com/spreadsheets/d/1YJAky7xNUpcAI4JvkFaaS2eC2GTn7eLFFoqRV5NhEMA/edit',
  },
  {
    label: 'Cronograma e Etapas do TCC',
    description: 'Datas, prazos e marcos do processo de TCC 1 e TCC 2.',
    url: 'https://docs.google.com/spreadsheets/d/1jGC1pcBySaH3vqPAeseg2hvK_U-QL7Tu/edit',
  },
]

export function CalendariosPage() {
  return (
    <PageShell icon="📅" title="Calendários Acadêmicos"
      subtitle="Cronogramas, ofertas e prazos do curso de Sistemas de Informação — FASI/UFPA">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {calendarios.map(({ label, description, url }) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noreferrer"
            className="fasi-card p-6 flex items-start gap-4 hover:shadow-fasi-md transition-shadow group"
          >
            <div className="text-3xl shrink-0">📅</div>
            <div>
              <p className="font-semibold text-sm text-foreground group-hover:text-fasi-600 transition-colors mb-1">
                {label}
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
              <span className="inline-block mt-3 text-xs text-fasi-500 font-medium">
                Abrir no Google Sheets →
              </span>
            </div>
          </a>
        ))}
      </div>
    </PageShell>
  )
}
