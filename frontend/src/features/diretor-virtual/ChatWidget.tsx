import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Bot, User, Send, X, Loader2, MessageCircle } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import { submitJson } from '@/shared/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const INITIAL_MESSAGE: Message = {
  role: 'assistant',
  content: 'Olá! Sou o Diretor Virtual da FASI. Posso ajudá-lo com dúvidas sobre matrículas, TCC, ACC, estágio, PPC e normas do curso. Como posso ajudar?',
}

export function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [open, messages])

  const mutation = useMutation({
    mutationFn: (mensagem: string) =>
      submitJson('/api/v1/diretor-virtual/chat', { mensagem }, 300_000),
    onSuccess: (data: { resposta: string }) => {
      setMessages(prev => [...prev, { role: 'assistant', content: data.resposta }])
    },
    onError: () => {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Desculpe, estou indisponível no momento. Tente novamente em instantes.' },
      ])
    },
  })

  const send = () => {
    const text = input.trim()
    if (!text || mutation.isPending) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    mutation.mutate(text)
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

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
                <p className="text-white/70 text-xs">Assistente Acadêmico FASI</p>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-white/70 hover:text-white transition-colors"
              aria-label="Fechar chat"
            >
              <X className="w-4 h-4" />
            </button>
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
                  {m.content}
                </div>
              </div>
            ))}

            {mutation.isPending && (
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

          {/* Input */}
          <div className="border-t border-border p-3 bg-white flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Digite sua dúvida... (Enter para enviar)"
              rows={2}
              disabled={mutation.isPending}
              className="flex-1 resize-none text-xs rounded-xl border border-border px-3 py-2
                         focus:outline-none focus:ring-2 focus:ring-fasi-400 focus:border-transparent
                         placeholder:text-muted-foreground disabled:opacity-50"
            />
            <button
              onClick={send}
              disabled={!input.trim() || mutation.isPending}
              className="w-8 h-8 rounded-xl bg-fasi-500 hover:bg-fasi-600 disabled:opacity-40
                         flex items-center justify-center transition-colors shrink-0"
            >
              {mutation.isPending
                ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                : <Send className="w-3.5 h-3.5 text-white" />
              }
            </button>
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
