import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { PageShell } from '@/shared/components/PageShell'
import { submitJson } from '@/shared/lib/api'
import { cn } from '@/shared/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function DiretorVirtual() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Olá! Sou o Diretor Virtual da FASI. Posso ajudá-lo com dúvidas sobre matrículas, TCC, ACC, estágio, PPC e normas do curso. Como posso ajudar?',
    },
  ])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const mutation = useMutation({
    mutationFn: (mensagem: string) => submitJson('/api/v1/diretor-virtual/chat', { mensagem }, 300_000),
    onSuccess: (data: { resposta: string }) => {
      setMessages(prev => [...prev, { role: 'assistant', content: data.resposta }])
    },
    onError: () => toast.error('Diretor Virtual indisponível no momento.'),
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

  return (
    <PageShell icon="🤖" title="Diretor Virtual"
      subtitle="Assistente inteligente para dúvidas acadêmicas — PPC, TCC, ACC, Estágio e mais">
      <div className="fasi-card flex flex-col h-[600px]">
        {/* Mensagens */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={cn('flex gap-3', m.role === 'user' ? 'flex-row-reverse' : 'flex-row')}>
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
                m.role === 'user' ? 'bg-fasi-500' : 'bg-muted',
              )}>
                {m.role === 'user'
                  ? <User className="w-4 h-4 text-white" />
                  : <Bot className="w-4 h-4 text-fasi-500" />
                }
              </div>
              <div className={cn(
                'max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed',
                m.role === 'user'
                  ? 'bg-fasi-500 text-white rounded-tr-sm'
                  : 'bg-muted text-foreground rounded-tl-sm',
              )}>
                {m.content}
              </div>
            </div>
          ))}

          {mutation.isPending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Bot className="w-4 h-4 text-fasi-500" />
              </div>
              <div className="bg-muted rounded-xl rounded-tl-sm px-4 py-3">
                <Loader2 className="w-4 h-4 animate-spin text-fasi-500" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border p-4 flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Digite sua dúvida... (Enter para enviar)"
            rows={2}
            className="fasi-input flex-1 resize-none"
            disabled={mutation.isPending}
          />
          <button
            onClick={send}
            disabled={!input.trim() || mutation.isPending}
            className="fasi-btn-primary px-4 self-end"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </PageShell>
  )
}
