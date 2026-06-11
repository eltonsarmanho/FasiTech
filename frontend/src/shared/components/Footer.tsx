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
      </div>
    </footer>
  )
}
