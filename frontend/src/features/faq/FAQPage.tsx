import { ReactNode, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { PageShell } from '@/shared/components/PageShell'
import { cn } from '@/shared/lib/utils'

type FAQItem = { q: string; a: ReactNode }

const faqs: { category: string; items: FAQItem[] }[] = [
  {
    category: '1. Matrícula em Disciplinas',
    items: [
      { q: 'Qual disciplina devo me matricular?', a: 'Consulte o calendário de ofertas do curso disponível no site da Faculdade.' },
      { q: 'Quando será a oferta de uma determinada disciplina?', a: 'Consulte o calendário de ofertas do curso disponível no site da Faculdade.' },
      { q: 'Como solicitar aumento de créditos?', a: 'Entre em contato diretamente com o Diretor ou Secretário por e-mail ou mensagem.' },
      { q: 'O sistema não permite que eu faça determinadas disciplinas devido a conflito de horário. O que devo fazer?', a: 'Matricule-se em algumas disciplinas e deixe outras para o próximo período. Seja paciente, você não pode conquistar o mundo de uma vez.' },
      { q: 'Reprovei em uma disciplina no semestre passado. O que devo fazer?', a: 'Estude e espere a próxima oferta da disciplina em um turno diferente do seu. Você poderá cursar essa disciplina novamente quando ela for ofertada (consulte o quadro de ofertas no site do curso).' },
      { q: 'Me inscrevi em uma disciplina por engano que não faz parte da minha grade. O que devo fazer?', a: 'Retorne à tela de matrícula e remova a disciplina indesejada. Atenção na próxima vez!' },
      {
        q: 'Recebi a mensagem "NÃO É POSSÍVEL REALIZAR A MATRÍCULA PORQUE VOCÊ NÃO PREENCHEU A AVALIAÇÃO INSTITUCIONAL". O que devo fazer?',
        a: 'Você deve completar a Avaliação Institucional antes de realizar a matrícula. Vá na aba de "Ensino", selecione a opção "Avaliação Institucional" e preencha a avaliação.',
      },
      {
        q: 'Nenhuma disciplina aparece no SIGAA. O que devo fazer?',
        a: (
          <div>
            <p>Adicione as disciplinas manualmente seguindo estes passos:</p>
            <ol className="list-decimal pl-5 mt-2 space-y-1">
              <li>Clique em <strong>"Adicionar Turma"</strong></li>
              <li>Selecione <strong>"Adicionar disciplinas por código"</strong></li>
              <li>Os códigos estão disponíveis na lista de ofertas da FASI</li>
            </ol>
          </div>
        ),
      },
    ],
  },
  {
    category: '2. Estágio e TCC',
    items: [
      {
        q: 'Como funcionam as disciplinas de Estágio I e II?',
        a: (
          <div className="space-y-1">
            <p>Essas disciplinas estão no quadro de ofertas do curso (no site), mas <strong>não são ofertadas diretamente no SIGAA</strong>.</p>
            <p>A direção, junto com a secretaria, realizará a matrícula durante o período definido no quadro de oferta.</p>
          </div>
        ),
      },
      { q: 'Há restrição para Atividades Flexibilizadas em Estágio/TCC?', a: 'Sim. A reserva de vagas para as atividades flexibilizadas não se aplica a disciplinas como TCC, estágios e práticas que sejam regulamentadas por normas específicas. Nesses casos, o aluno deve seguir as regras de seu curso.' },
      { q: 'Quais são os requisitos para iniciar o TCC 1?', a: 'Você deve ter completado todos os pré-requisitos curriculares. Consulte o PPC do curso disponível neste portal para verificar.' },
      { q: 'Como submeto meu TCC?', a: 'Acesse o formulário de TCC neste portal, preencha os dados e faça o upload dos documentos em PDF.' },
      { q: 'Quais documentos são necessários para o TCC 2?', a: 'TCC 2 requer no mínimo 2 arquivos: (1) TCC Final em PDF e (2) Declaração de Autoria + Termo de Autorização (pode ser um único PDF combinado).' },
      { q: 'Como submeto meu relatório de estágio?', a: 'Acesse o formulário de estágio neste portal e faça o upload do Relatório Final em PDF.' },
    ],
  },
  {
    category: '3. Atividades Flexibilizadas (Aproveitamento de Estudos)',
    items: [
      {
        q: 'O aluno pode fazer disciplina (Atividade Flexibilizada) fora da UFPA? Como será computada no SIGAA?',
        a: (
          <ul className="list-disc pl-5 space-y-1">
            <li>Sim, o aluno pode cursar disciplinas em outras Instituições de Ensino Superior (IES).</li>
            <li>Para que as horas sejam validadas, a disciplina deve ser de uma área de conhecimento relevante para a sua formação.</li>
            <li>A Unidade Acadêmica da UFPA ou da outra IES que ofertar a disciplina será a responsável por computar a carga horária.</li>
            <li>A matrícula e o registro no SIGAA serão realizados de acordo com os procedimentos específicos definidos para o aproveitamento de estudos externos.</li>
          </ul>
        ),
      },
      {
        q: 'O aluno pode fazer disciplina na UFPA, mas fora do Campus de Cametá? Via SIGAA?',
        a: (
          <ul className="list-disc pl-5 space-y-1">
            <li>Sim, é possível cursar disciplinas em outros campi da UFPA.</li>
            <li>A matrícula nas atividades flexibilizadas dentro da UFPA será feita diretamente pelo SIGAA.</li>
            <li>Os cursos de graduação da UFPA podem disponibilizar vagas de livre acesso em suas disciplinas, destinadas a alunos de cursos com essa modalidade de flexibilização.</li>
          </ul>
        ),
      },
      {
        q: 'O aluno pode fazer quais tipos de disciplinas flexibilizadas? Existe alguma restrição?',
        a: (
          <ul className="list-disc pl-5 space-y-1">
            <li>O aluno pode escolher as disciplinas de acordo com seus interesses e preferências.</li>
            <li><strong>Restrição principal:</strong> A reserva de vagas para as atividades flexibilizadas não se aplica a disciplinas como TCC, estágios e práticas regulamentadas por normas específicas. Nesses casos, o aluno deve seguir as regras de seu curso.</li>
          </ul>
        ),
      },
      { q: 'O que são ACCs e como envio?', a: 'Atividades Curriculares Complementares são atividades extracurriculares que complementam sua formação: cursos, eventos, participação em projetos, estágios não obrigatórios, etc. Consolide todos os certificados em um único arquivo PDF e submeta pelo formulário de ACC neste portal.' },
    ],
  },
  {
    category: '4. Outorga de Grau e Diploma',
    items: [
      {
        q: 'Como iniciar o processo de Outorga de Grau (ou Registro de Diploma)?',
        a: (
          <ol className="list-decimal pl-5 space-y-1">
            <li>Entre no <strong>SIGAA</strong>.</li>
            <li>Localize o menu <strong>"Ensino"</strong>.</li>
            <li>Localize a opção <strong>"Solicitação Validação de Documentos para Registro de Diploma"</strong>.</li>
            <li>Anexe os seguintes documentos: Diploma de Ensino Médio, Carteira de Identidade e Declaração de Quitação da Biblioteca.</li>
          </ol>
        ),
      },
    ],
  },
  {
    category: '5. Acesso a Periódicos Científicos (CAPES)',
    items: [
      {
        q: 'Como posso acessar artigos e periódicos científicos usando meu login institucional da UFPA?',
        a: (
          <div className="space-y-3">
            <p>O acesso ao acervo de periódicos da CAPES é um benefício para toda a comunidade acadêmica da UFPA. Para utilizar, siga os passos abaixo:</p>
            <ol className="list-decimal pl-5 space-y-1">
              <li>Acesse o site: <strong>https://www.periodicos.capes.gov.br/</strong></li>
              <li>Clique em <strong>"ACESSO CAFE"</strong> no menu superior da página.</li>
              <li>Na tela da "Comunidade Acadêmica Federada", selecione <strong>"UFPA"</strong> e clique em <strong>"Enviar"</strong>.</li>
              <li>Informe seu e-mail institucional completo (ex: <code className="bg-muted px-1 rounded">seulogin@ufpa.br</code>) e senha.</li>
              <li>Após o login, você terá acesso remoto a todas as bases de periódicos e artigos científicos assinados pela CAPES.</li>
            </ol>
            <div>
              <p className="font-medium mb-1">Como buscar uma base específica (ex: IEEE Xplore):</p>
              <ol className="list-decimal pl-5 space-y-1">
                <li>No menu, navegue até <strong>Acervo → Lista de bases e coleções</strong>.</li>
                <li>Na barra de busca, digite <strong>"IEEE"</strong> e clique em "Enviar".</li>
                <li>Clique em <strong>IEEE Xplore Digital Library</strong> nos resultados.</li>
              </ol>
            </div>
          </div>
        ),
      },
    ],
  },
  {
    category: 'Contato',
    items: [
      { q: 'Como entro em contato com a secretaria?', a: 'Pelo e-mail fasicuntins@ufpa.br ou pessoalmente na secretaria da FASI no campus de Cametá.' },
    ],
  },
]

function FAQItemComp({ q, a }: FAQItem) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full text-left px-4 py-3.5 flex items-center justify-between gap-3
                   hover:bg-muted/40 transition-colors"
      >
        <span className="text-sm font-medium text-foreground">{q}</span>
        <ChevronDown className={cn('w-4 h-4 text-fasi-500 shrink-0 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="px-4 pb-4 pt-1 text-sm text-muted-foreground leading-relaxed border-t border-border bg-muted/20">
          {a}
        </div>
      )}
    </div>
  )
}

export function FAQPage() {
  return (
    <PageShell icon="❓" title="Perguntas Frequentes"
      subtitle="Respostas para as dúvidas mais comuns sobre matrículas, disciplinas, aproveitamento de estudos e outros processos acadêmicos">
      <div className="space-y-8">
        {faqs.map(({ category, items }) => (
          <section key={category}>
            <h2 className="fasi-section-title">{category}</h2>
            <div className="space-y-2 mt-4">
              {items.map(item => <FAQItemComp key={item.q} {...item} />)}
            </div>
          </section>
        ))}
      </div>
    </PageShell>
  )
}
