import { BookOpenCheck, ExternalLink, Mail } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/shared/components/PageShell'

const Section = ({ title, children }: { title: string; children: ReactNode }) => (
  <section className="rounded-xl border border-border bg-white p-5 md:p-7 shadow-sm">
    <h2 className="font-display text-lg font-bold text-[#1A3A6B]">{title}</h2>
    <div className="mt-3 space-y-3 text-sm leading-6 text-[#475569]">{children}</div>
  </section>
)

export function TermosServicoPage() {
  return (
    <PageShell
      title="Termos de Serviço"
      subtitle="Regras para uso responsável do portal acadêmico FasiTech."
      icon="📘"
    >
      <div className="mx-auto max-w-4xl space-y-5">
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-5 text-sm leading-6 text-[#334155]">
          <div className="flex gap-3">
            <BookOpenCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#1A3A6B]" aria-hidden />
            <p>Ao acessar ou utilizar o FasiTech, você concorda com estes Termos de Serviço. Última atualização: <strong>20 de julho de 2026</strong>.</p>
          </div>
        </div>

        <Section title="1. Finalidade do portal">
          <p>O FasiTech é um portal de apoio às atividades acadêmicas e administrativas da Faculdade de Sistemas de Informação (FASI) da Universidade Federal do Pará (UFPA). Ele disponibiliza formulários, consultas, documentos, calendários, informações e recursos de suporte à comunidade acadêmica.</p>
          <p>O portal não substitui os sistemas oficiais, normas, editais, decisões administrativas ou comunicações institucionais da UFPA. Quando houver divergência, prevalecem os canais e atos oficiais da Universidade.</p>
        </Section>

        <Section title="2. Uso adequado">
          <p>Você deve utilizar o portal de modo lícito, ético e compatível com sua finalidade acadêmica. Ao enviar uma solicitação, é sua responsabilidade fornecer dados verdadeiros, atuais e pertinentes ao serviço solicitado, além de conferir os documentos e informações antes do envio.</p>
          <p>Não é permitido usar o FasiTech para:</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>enviar conteúdo ilegal, ofensivo, malicioso ou que viole direitos de terceiros;</li>
            <li>acessar áreas, dados ou contas sem autorização;</li>
            <li>interferir no funcionamento, testar vulnerabilidades ou tentar contornar controles de segurança;</li>
            <li>enviar documentos de outra pessoa sem a devida autorização ou finalidade institucional.</li>
          </ul>
        </Section>

        <Section title="3. Solicitações e documentos">
          <p>O envio de um formulário registra uma solicitação para análise pela FASI e pelos setores competentes; ele não representa, por si só, matrícula, aprovação, emissão de documento, deferimento ou confirmação de qualquer direito acadêmico.</p>
          <p>As decisões e os prazos dependem das normas aplicáveis, da conferência das informações e da atuação do setor responsável. A FASI poderá solicitar complementação, corrigir registros ou recusar arquivos que estejam incompletos, ilegíveis, incompatíveis com o serviço ou em desacordo com as regras institucionais.</p>
        </Section>

        <Section title="4. Recursos de inteligência artificial">
          <p>Algumas funcionalidades podem usar inteligência artificial para apoiar a leitura de documentos ou responder perguntas, como o Diretor Virtual. As respostas e análises são auxiliares, podem conter imprecisões e não constituem orientação oficial, decisão acadêmica ou parecer definitivo.</p>
          <p>Não envie ao chat ou a campos livres dados pessoais sensíveis, senhas ou informações de terceiros que não sejam estritamente necessárias. Para orientações formais, utilize os canais oficiais da FASI e da UFPA.</p>
        </Section>

        <Section title="5. Disponibilidade e segurança">
          <p>Buscamos manter o portal disponível e seguro, mas podem ocorrer interrupções temporárias por manutenção, atualizações, falhas técnicas ou fatores externos. Sempre que necessário, o acesso a funcionalidades poderá ser limitado ou suspenso para preservar a segurança e a continuidade do serviço.</p>
          <p>Você deve proteger suas credenciais e dispositivos, não compartilhar tokens ou senhas e comunicar à FASI qualquer suspeita de uso indevido ou falha de segurança.</p>
        </Section>

        <Section title="6. Propriedade intelectual e conteúdo institucional">
          <p>O código, identidade visual, textos, documentos e demais conteúdos do portal são protegidos pelas normas aplicáveis e podem pertencer à UFPA, à FASI ou aos respectivos titulares. É permitida a utilização para fins pessoais, educacionais e institucionais compatíveis com o portal, sem remover créditos ou atribuir autoria indevidamente.</p>
          <p>Documentos enviados por você permanecem sob sua responsabilidade quanto à autoria, veracidade e às permissões necessárias para seu uso no procedimento acadêmico.</p>
        </Section>

        <Section title="7. Privacidade e proteção de dados">
          <p>O tratamento de dados pessoais no FasiTech segue a legislação aplicável e a política institucional da UFPA. Leia nossa <Link to="/privacidade" className="font-medium text-[#2563EB] hover:underline">Política de Privacidade</Link> para conhecer as finalidades, os compartilhamentos, os prazos e os canais para exercer seus direitos.</p>
          <p>Os Termos observam, entre outras normas aplicáveis, o Marco Civil da Internet e as diretrizes institucionais da UFPA.</p>
        </Section>

        <Section title="8. Alterações e contato">
          <p>Estes termos podem ser atualizados para refletir mudanças no portal, em seus serviços ou na legislação. A versão vigente ficará disponível nesta página, com a respectiva data de atualização.</p>
          <p>Em caso de dúvida sobre o uso do FasiTech, entre em contato com a FASI: <a href="mailto:fasicuntins@ufpa.br" className="font-medium text-[#2563EB] hover:underline">fasicuntins@ufpa.br</a>. Para informações institucionais de proteção de dados, consulte a <a href="https://lgpd.ufpa.br/" target="_blank" rel="noreferrer" className="font-medium text-[#2563EB] hover:underline">página de LGPD da UFPA <ExternalLink className="inline h-3.5 w-3.5" aria-hidden /></a>.</p>
          <a href="mailto:fasicuntins@ufpa.br" className="inline-flex items-center gap-2 font-medium text-[#2563EB] hover:underline"><Mail className="h-4 w-4" aria-hidden /> fasicuntins@ufpa.br</a>
        </Section>
      </div>
    </PageShell>
  )
}
