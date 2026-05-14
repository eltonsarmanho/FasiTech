export function Footer() {
  return (
    <footer className="border-t border-border bg-white py-6 mt-8">
      <div className="container max-w-6xl mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>
          Desenvolvido por{' '}
          <a
            href="https://www.linkedin.com/in/elton-sarmanho-836553185/"
            target="_blank"
            rel="noreferrer"
            className="font-medium text-fasi-500 hover:text-fasi-600 transition-colors"
          >
            Elton Sarmanho
          </a>
          {' '}— FASI / UFPA Cametá
        </p>
        <p className="mt-1 text-xs">
          Para dúvidas:{' '}
          <a href="mailto:fasicuntins@ufpa.br" className="hover:text-fasi-500 transition-colors">
            fasicuntins@ufpa.br
          </a>
        </p>
      </div>
    </footer>
  )
}
