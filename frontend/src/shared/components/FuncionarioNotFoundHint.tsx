import { Info } from 'lucide-react'

const FASI_EMAIL = 'fasicuntins@ufpa.br'

/**
 * Aviso padrão exibido abaixo dos seletores de funcionário. Orienta o usuário
 * a solicitar o cadastro à FASI caso o nome desejado não apareça na lista.
 */
export function FuncionarioNotFoundHint() {
  const assunto = encodeURIComponent('Solicitação de cadastro de funcionário')
  const corpo = encodeURIComponent(
    'Olá, solicito o cadastro do seguinte funcionário no sistema FasiTech:\n\n' +
      '- Nome:\n' +
      '- Filiação:\n' +
      '- E-mail:\n' +
      '- Telefone (WhatsApp):\n' +
      '- Titulação (Doutorado/Mestrado/Especialista/Graduação):\n',
  )
  return (
    <p className="text-xs text-muted-foreground mt-1.5 flex items-start gap-1.5">
      <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
      <span>
        Não encontrou o nome na lista? Envie um e-mail para{' '}
        <a
          href={`mailto:${FASI_EMAIL}?subject=${assunto}&body=${corpo}`}
          className="underline hover:opacity-80 transition-opacity"
          style={{ color: '#2563EB' }}
        >
          {FASI_EMAIL}
        </a>{' '}
        com os dados a serem cadastrados: <strong>Nome, Filiação, e-mail, Telefone e Titulação</strong>.
      </span>
    </p>
  )
}
