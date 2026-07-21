import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="bg-white border-t border-border mt-8 py-6">
      <div className="container max-w-6xl mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>
          Desenvolvido por{' '}
          <a
            href="https://www.linkedin.com/in/elton-sarmanho-836553185/"
            target="_blank"
            rel="noreferrer"
            className="font-medium transition-colors hover:underline"
            style={{ color: '#2563EB' }}
          >
            Elton Sarmanho
          </a>
        </p>
        <p className="mt-1 text-xs">
          Para dúvidas:{' '}
          <a href="mailto:fasicuntins@ufpa.br" className="hover:underline" style={{ color: '#2563EB' }}>
            fasicuntins@ufpa.br
          </a>
        </p>
        <p className="mt-2 flex justify-center gap-3 text-xs">
          <Link to="/privacidade" className="hover:underline" style={{ color: '#2563EB' }}>
            Política de Privacidade
          </Link>
          <Link to="/termos-de-servico" className="hover:underline" style={{ color: '#2563EB' }}>
            Termos de Serviço
          </Link>
        </p>
      </div>
    </footer>
  )
}
