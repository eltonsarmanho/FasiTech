import { useState, useRef, useEffect, useCallback } from 'react'
import { Bot, User, Send, X, Loader2, MessageCircle, RefreshCw, Ticket } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/shared/lib/utils'

// Chatwoot SDK global
declare global {
  interface Window {
    chatwootSDK?: { run: (opts: { websiteToken: string; baseUrl: string }) => void }
    $chatwoot?: {
      open: () => void
      setUser: (id: string, attrs: { name?: string; email?: string }) => void
      reset: () => void
    }
  }
}

const CHATWOOT_BASE_URL = 'https://chatwoot.fasitech.cameta.ufpa.br'
const CHATWOOT_TOKEN = 'oUy6xunsEJMzcXDvzscMHj7M'

let chatwootLoadPromise: Promise<void> | null = null

function loadChatwootSDK(): Promise<void> {
  // Evita múltiplas tentativas simultâneas
  if (chatwootLoadPromise) return chatwootLoadPromise

  // Se já está carregado, retorna imediatamente
  if (window.chatwootSDK) {
    return Promise.resolve()
  }

  chatwootLoadPromise = new Promise((resolve, reject) => {
    if (document.getElementById('chatwoot-sdk')) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.id = 'chatwoot-sdk'
    script.src = `${CHATWOOT_BASE_URL}/packs/js/sdk.js`
    script.async = true
    script.type = 'module'

    script.onload = () => {
      // Aguarda o SDK estar disponível
      const waitForSDK = setInterval(() => {
        if (window.chatwootSDK) {
          clearInterval(waitForSDK)
          try {
            window.chatwootSDK.run({ websiteToken: CHATWOOT_TOKEN, baseUrl: CHATWOOT_BASE_URL })
            resolve()
          } catch (err) {
            console.error('Erro ao inicializar Chatwoot:', err)
            reject(err)
          }
        }
      }, 100)

      // Timeout de 10s
      setTimeout(() => {
        clearInterval(waitForSDK)
        reject(new Error('Chatwoot SDK não inicializou a tempo'))
      }, 10000)
    }

    script.onerror = () => {
      console.error('Falha ao carregar SDK do Chatwoot de:', script.src)
      reject(new Error('Falha ao carregar SDK do Chatwoot'))
    }

    document.head.appendChild(script)
  })

  chatwootLoadPromise.catch(() => {
    chatwootLoadPromise = null // Reset para próximas tentativas
  })

  return chatwootLoadPromise
}

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatbotResponse {
  session_id: string
  response: string
  options: string[] | null
  ticket_id: string | null
  state: string
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [ticketId, setTicketId] = useState<string | null>(null)
  const [chatState, setChatState] = useState<string>('idle')
  const [options, setOptions] = useState<string[] | null>(null)
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const startSession = useCallback(async () => {
    setLoading(true)
    setMessages([])
    setTicketId(null)
    setOptions(null)
    setSessionId(null)
    try {
      const data = await apiPost<ChatbotResponse>('/api/v1/chatbot/start', {})
      setSessionId(data.session_id)
      setChatState(data.state)
      setOptions(data.options ?? null)
      setMessages([{ role: 'assistant', content: data.response }])
    } catch {
      setMessages([{ role: 'assistant', content: 'Serviço temporariamente indisponível. Tente novamente.' }])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open && messages.length === 0) {
      startSession()
    }
  }, [open, messages.length, startSession])

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      if (chatState !== 'escalated' && chatState !== 'ended') {
        setTimeout(() => inputRef.current?.focus(), 100)
      }
    }
  }, [open, messages, chatState])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading || !sessionId) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    setOptions(null)
    setLoading(true)
    try {
      const data = await apiPost<ChatbotResponse>('/api/v1/chatbot/message', {
        session_id: sessionId,
        message: text,
      })
      setSessionId(data.session_id)
      setChatState(data.state)
      setOptions(data.options ?? null)
      if (data.ticket_id) setTicketId(data.ticket_id)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])

      // Se escalou para humano, abre o Chatwoot SDK para chat em tempo real
      if (data.state === 'escalated') {
        loadChatwootSDK()
          .then(() => {
            setTimeout(() => window.$chatwoot?.open(), 500)
          })
          .catch((err) => {
            console.error('Falha ao carregar Chatwoot:', err)
            setMessages(prev => [
              ...prev,
              { role: 'assistant', content: 'Erro ao conectar com atendimento humano. Por favor, tente novamente.' },
            ])
          })
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Erro ao processar mensagem. Tente novamente.' },
      ])
    } finally {
      setLoading(false)
    }
  }, [loading, sessionId])

  const send = () => sendMessage(input.trim())

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const isFinished = chatState === 'escalated' || chatState === 'ended'
  const unread = !open && messages.length > 1

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      {/* Painel do chat */}
      {open && (
        <div className="w-[340px] sm:w-[380px] flex flex-col rounded-2xl shadow-2xl border border-border
                        bg-white overflow-hidden animate-slide-up"
          style={{ height: '520px' }}>

          {/* Header */}
          <div className="fasi-header-gradient px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm leading-tight">Diretor Virtual</p>
                {ticketId
                  ? <p className="text-white/80 text-xs flex items-center gap-1"><Ticket className="w-3 h-3" />{ticketId}</p>
                  : <p className="text-white/70 text-xs">Assistente Acadêmico FASI</p>
                }
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isFinished && (
                <button
                  onClick={startSession}
                  className="text-white/70 hover:text-white transition-colors"
                  aria-label="Reiniciar conversa"
                  title="Nova conversa"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="text-white/70 hover:text-white transition-colors"
                aria-label="Fechar chat"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50">
            {messages.map((m, i) => (
              <div key={i} className={cn('flex gap-2', m.role === 'user' ? 'flex-row-reverse' : 'flex-row')}>
                <div className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5',
                  m.role === 'user' ? 'bg-fasi-500' : 'bg-white border border-border shadow-sm',
                )}>
                  {m.role === 'user'
                    ? <User className="w-3.5 h-3.5 text-white" />
                    : <Bot className="w-3.5 h-3.5 text-fasi-500" />
                  }
                </div>
                <div className={cn(
                  'max-w-[80%] rounded-2xl px-3 py-2 text-xs leading-relaxed shadow-sm',
                  m.role === 'user'
                    ? 'bg-fasi-500 text-white rounded-tr-sm'
                    : 'bg-white text-foreground rounded-tl-sm border border-border',
                )}>
                  {m.role === 'assistant' ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc pl-4 mb-1 space-y-0.5">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-4 mb-1 space-y-0.5">{children}</ol>,
                        li: ({ children }) => <li className="leading-snug">{children}</li>,
                        a: ({ href, children }) => (
                          <a href={href} target="_blank" rel="noreferrer" className="underline text-fasi-600 hover:text-fasi-700">{children}</a>
                        ),
                        code: ({ children }) => <code className="bg-gray-100 rounded px-1 font-mono text-[10px]">{children}</code>,
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  ) : (
                    m.content
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-2">
                <div className="w-7 h-7 rounded-full bg-white border border-border shadow-sm flex items-center justify-center">
                  <Bot className="w-3.5 h-3.5 text-fasi-500" />
                </div>
                <div className="bg-white rounded-2xl rounded-tl-sm px-3 py-2.5 border border-border shadow-sm">
                  <div className="flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-fasi-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-fasi-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-fasi-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick-reply options */}
          {options && options.length > 0 && !loading && (
            <div className="px-3 pb-2 bg-gray-50 flex flex-wrap gap-2">
              {options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(opt)}
                  className="text-xs px-3 py-1.5 rounded-full border border-fasi-300 text-fasi-600
                             hover:bg-fasi-50 hover:border-fasi-400 transition-colors"
                >
                  {opt}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="border-t border-border p-3 bg-white flex gap-2 items-end">
            {isFinished ? (
              <button
                onClick={startSession}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl
                           bg-fasi-500 hover:bg-fasi-600 text-white text-xs font-medium transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Nova conversa
              </button>
            ) : (
              <>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Digite aqui... (Enter para enviar)"
                  rows={2}
                  disabled={loading}
                  className="flex-1 resize-none text-xs rounded-xl border border-border px-3 py-2
                             focus:outline-none focus:ring-2 focus:ring-fasi-400 focus:border-transparent
                             placeholder:text-muted-foreground disabled:opacity-50"
                />
                <button
                  onClick={send}
                  disabled={!input.trim() || loading}
                  className="w-8 h-8 rounded-xl bg-fasi-500 hover:bg-fasi-600 disabled:opacity-40
                             flex items-center justify-center transition-colors shrink-0"
                >
                  {loading
                    ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                    : <Send className="w-3.5 h-3.5 text-white" />
                  }
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Botão flutuante */}
      <button
        onClick={() => setOpen(v => !v)}
        aria-label="Abrir Diretor Virtual"
        className="w-14 h-14 rounded-full fasi-header-gradient shadow-fasi-lg
                   flex items-center justify-center transition-transform hover:scale-105 active:scale-95 relative"
      >
        {open
          ? <X className="w-6 h-6 text-white" />
          : <MessageCircle className="w-6 h-6 text-white" />
        }
        {unread && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500
                           flex items-center justify-center text-white text-[10px] font-bold">
            {messages.length - 1}
          </span>
        )}
      </button>
    </div>
  )
}
