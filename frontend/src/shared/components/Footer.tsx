import seloSebrae from '@/assets/selo-sebrae.png'

export function Footer() {
  return (
    <footer className="border-t border-border bg-white py-6 mt-8">
      <div className="container max-w-6xl mx-auto px-4">
        {/* Selo Sebrae */}
        <div className="flex flex-col items-center gap-1 mb-4">
          <img
            src={seloSebrae}
            alt="Selo Sebrae — Prêmio Educador Transformador 2025"
            className="h-20 object-contain opacity-90 hover:opacity-100 transition-opacity"
            title="Prêmio Educador Transformador 2025 — Etapa Estadual Vencedor"
          />
          <p className="text-xs text-muted-foreground">
            2º Lugar em Gestão Educacional Transformadora · Prêmio Educador Transformador 3ª Edição
          </p>
        </div>

        <div className="text-center text-sm text-muted-foreground border-t border-border pt-4">
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
          </p>
          <p className="mt-1 text-xs">
            Para dúvidas:{' '}
            <a href="mailto:fasicuntins@ufpa.br" className="hover:text-fasi-500 transition-colors">
              fasicuntins@ufpa.br
            </a>
          </p>
        </div>
      </div>
    </footer>
  )
}
