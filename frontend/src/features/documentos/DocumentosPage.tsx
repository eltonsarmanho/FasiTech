import { PageShell } from '@/shared/components/PageShell'

const sections = [
  {
    title: 'PPC & ACC',
    links: [
      { label: 'Novo PPC — 2023', url: 'https://drive.google.com/file/d/1FX1ETtGQM47xcv_qE73GyuoEJTEhUJJk/view' },
      { label: 'PPC (Antigo)', url: 'https://drive.google.com/file/d/1QyDQB7rUwzSCQUkpwrjOg-6zKXh1PCL9/view' },
      { label: 'Nova Resolução das ACCs', url: 'https://drive.google.com/file/d/1JTH-RGtNjXghqfukl95vBmJSATIOXP7o/view' },
      { label: 'Anexo ACC', url: 'https://drive.google.com/file/d/1L4xfx73IMLWTfiJp8qE5KDg1hOzBEqc7/view' },
    ],
  },
  {
    title: 'TCC & Estágio',
    links: [
      { label: 'Diretrizes TCC FASI 2024', url: 'https://docs.google.com/document/d/125WbjVhAaAqGporWUcXmWZKXLV-QVN9B/edit' },
      { label: 'Form Indicação TCC 1 (Anexo I)', url: 'https://docs.google.com/document/d/1yuz3oDEvQ66jGcao6FtfClB0uoDhbLWt/edit' },
      { label: 'Modelo Pré-Projeto TCC 1', url: 'https://drive.google.com/file/d/10ncOkDrPkRJSqY9IzLD850qUwllXwHv7/view' },
      { label: 'Modelo Plano de Estágio', url: 'https://drive.google.com/file/d/1w6Q-JfYybV3Xf7LEU3K0U_dYjnQek7Uf/view' },
      { label: 'Modelo Relatório Final de Estágio', url: 'https://drive.google.com/file/d/1JCQG1klfekTTaxg-hXEyhJfDZ1OcYCAE/view' },
    ],
  },
  {
    title: 'Regimento',
    links: [
      { label: 'Regimento Interno', url: 'https://drive.google.com/file/d/1FItcWP485eOyFRPTKisTxUL--KbbOv1N/view' },
      { label: 'Regimento do Laboratório de SI', url: 'https://drive.google.com/file/d/1L2_jkfUYybO8yraQqN-ploqdZTRjVJQc/view' },
    ],
  },
]

export function DocumentosPage() {
  return (
    <PageShell icon="📚" title="Documentos Oficiais"
      subtitle="Documentos institucionais do curso de Sistemas de Informação — FASI/UFPA">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map(({ title, links }) => (
          <div key={title} className="fasi-card p-6">
            <h2 className="font-semibold text-foreground mb-4 text-sm flex items-center gap-2">
              <span className="w-1 h-4 rounded-full bg-fasi-500 inline-block" />
              {title}
            </h2>
            <ul className="space-y-2.5">
              {links.map(({ label, url }) => (
                <li key={url}>
                  <a
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-fasi-600 hover:text-fasi-700 hover:underline transition-colors"
                  >
                    <span className="text-base shrink-0">📄</span>
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </PageShell>
  )
}
