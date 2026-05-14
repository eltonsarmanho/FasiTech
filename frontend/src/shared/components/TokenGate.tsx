import { useState } from 'react'
import { Lock } from 'lucide-react'

interface Props {
  storageKey: string
  children: React.ReactNode
}

/** Exibe um campo de token antes de mostrar o conteúdo protegido.
 *  O token é salvo em localStorage e enviado como Bearer pelo apiAuth. */
export function TokenGate({ storageKey, children }: Props) {
  const [authed, setAuthed] = useState(() => !!localStorage.getItem(storageKey))
  const [input, setInput] = useState('')
  const [error, setError] = useState('')

  if (authed) {
    return (
      <>
        <div className="mb-4 flex justify-end">
          <button
            className="fasi-btn-outline py-1 px-3 text-xs"
            onClick={() => { localStorage.removeItem(storageKey); setAuthed(false) }}
          >
            Sair
          </button>
        </div>
        {children}
      </>
    )
  }

  const handleSubmit = () => {
    if (!input.trim()) { setError('Informe o token.'); return }
    // fasitech_token é a chave usada pelo apiAuth para enviar o Bearer
    localStorage.setItem('fasitech_token', input.trim())
    localStorage.setItem(storageKey, '1')
    setAuthed(true)
  }

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="fasi-card max-w-sm w-full p-8 text-center space-y-5">
        <div className="flex justify-center">
          <Lock className="w-10 h-10 text-fasi-500" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Acesso Restrito</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Insira o <strong>FASI_TOKEN</strong> para continuar.
          </p>
        </div>
        <div className="space-y-3">
          <input
            type="password"
            className="fasi-input"
            placeholder="Cole o FASI_TOKEN aqui..."
            value={input}
            onChange={e => { setInput(e.target.value); setError('') }}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button className="fasi-btn-primary w-full" onClick={handleSubmit}>
            Entrar
          </button>
        </div>
      </div>
    </div>
  )
}
