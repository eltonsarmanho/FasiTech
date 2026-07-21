import { ExternalLink, Mail, ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'
import { PageShell } from '@/shared/components/PageShell'

const Section = ({ title, children }: { title: string; children: ReactNode }) => (
  <section className="rounded-xl border border-border bg-white p-5 md:p-7 shadow-sm">
    <h2 className="font-display text-lg font-bold text-[#1A3A6B]">{title}</h2>
    <div className="mt-3 space-y-3 text-sm leading-6 text-[#475569]">{children}</div>
  </section>
)

export function PoliticaPrivacidadePage() {
  return (
    <PageShell
      title="Política de Privacidade"
      subtitle="Como o FasiTech trata dados pessoais no apoio às atividades acadêmicas da FASI/UFPA."
      icon="🔒"
    >
      <div className="mx-auto max-w-4xl space-y-5">
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-5 text-sm leading-6 text-[#334155]">
          <div className="flex gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#1A3A6B]" aria-hidden />
            <p>
              Esta política complementa a Política de Privacidade e Proteção de Dados Pessoais da UFPA e descreve os tratamentos realizados neste portal. Última atualização: <strong>20 de julho de 2026</strong>.
            </p>
          </div>
        </div>

        <Section title="1. Quem é responsável pelos dados">
          <p>
            A Universidade Federal do Pará (UFPA), por meio da Faculdade de Sistemas de Informação (FASI), é responsável pelas decisões sobre o tratamento de dados pessoais realizado no FasiTech, para as finalidades acadêmicas e administrativas descritas nesta página.
          </p>
          <p>
            Para assuntos relacionados a um formulário ou serviço da FASI, escreva para <a className="font-medium text-[#2563EB] hover:underline" href="mailto:fasicuntins@ufpa.br">fasicuntins@ufpa.br</a>. Para informações institucionais sobre privacidade e canais da UFPA, consulte a <a className="font-medium text-[#2563EB] hover:underline" href="https://lgpd.ufpa.br/" target="_blank" rel="noreferrer">página de LGPD da UFPA <ExternalLink className="inline h-3.5 w-3.5" aria-hidden /></a>.
          </p>
        </Section>

        <Section title="2. Dados que tratamos">
          <p>Conforme o serviço utilizado, o FasiTech pode tratar:</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>dados de identificação e contato, como nome, matrícula, e-mail e telefone;</li>
            <li>dados acadêmicos e administrativos, como turma, polo, período, disciplina, orientador, projeto, solicitação e situação de submissão;</li>
            <li>documentos e arquivos enviados nos formulários, inclusive trabalhos, históricos, relatórios e comprovantes;</li>
            <li>respostas a avaliações e pesquisas institucionais;</li>
            <li>no formulário socioeconômico, dados como raça/cor, deficiência, renda e informações relacionadas à saúde mental, que podem ser dados pessoais sensíveis pela LGPD;</li>
            <li>mensagens enviadas ao Diretor Virtual e dados técnicos necessários ao funcionamento da sessão.</li>
          </ul>
          <p>Pedimos que você não inclua, em campos livres ou anexos, dados pessoais de terceiros que não sejam necessários à solicitação.</p>
        </Section>

        <Section title="3. Finalidades e bases legais">
          <p>Os dados são usados para receber, analisar e acompanhar solicitações acadêmicas; emitir documentos; organizar ofertas, projetos e defesas; comunicar estudantes, docentes e setores responsáveis; produzir informações gerenciais; e prestar suporte pelos serviços do portal.</p>
          <p>Por ser um serviço da UFPA, o tratamento ocorre principalmente para a execução de políticas públicas, atribuições institucionais, procedimentos acadêmicos e cumprimento de obrigações legais ou regulatórias, nos termos da LGPD. Quando o tratamento depender de consentimento, ele será solicitado de forma específica. Dados sensíveis recebem tratamento restrito à finalidade informada e às hipóteses legais aplicáveis.</p>
        </Section>

        <Section title="4. Compartilhamento e operadores">
          <p>O acesso é limitado às pessoas e setores da UFPA que precisam dos dados para tratar a solicitação, como FASI, secretaria, coordenações, docentes envolvidos e áreas administrativas competentes.</p>
          <p>Para viabilizar funcionalidades, o portal pode utilizar serviços contratados ou institucionais de armazenamento e planilhas do Google, envio de e-mail e provedores de inteligência artificial. Arquivos e informações estritamente necessários podem ser encaminhados a esses operadores para armazenamento, comunicação, processamento ou resposta assistida. O compartilhamento não é feito para publicidade ou venda de dados.</p>
        </Section>

        <Section title="5. Armazenamento, segurança e prazo">
          <p>As submissões e seus metadados podem ser armazenados em banco de dados institucional e, conforme o formulário, os arquivos podem ser mantidos em repositórios institucionais ou em serviços de nuvem utilizados pela UFPA. O acesso deve observar a necessidade da atividade e controles administrativos e técnicos aplicáveis.</p>
          <p>Os dados são mantidos pelo tempo necessário para atender às finalidades acadêmicas e administrativas, cumprir obrigações legais, regulatórias, de prestação de contas e de arquivo público, ou defender direitos em processos. A eliminação poderá não ser possível quando houver dever legal de conservação ou outra hipótese prevista em lei.</p>
        </Section>

        <Section title="6. Seus direitos">
          <p>Nos limites e procedimentos aplicáveis ao Poder Público, você pode solicitar confirmação de tratamento, acesso, correção de dados incompletos ou desatualizados, informação sobre compartilhamentos, anonimização, bloqueio ou eliminação de dados desnecessários ou tratados em desconformidade, além de outros direitos previstos na LGPD. Também pode revogar consentimentos quando essa for a base legal do tratamento.</p>
          <p>Para exercer um direito, envie um pedido para o canal da FASI acima, identificando o formulário ou serviço e o direito desejado. Poderemos solicitar informações adicionais para confirmar sua identidade e proteger seus dados. Caso necessário, você pode recorrer aos canais institucionais da UFPA e à Autoridade Nacional de Proteção de Dados (ANPD).</p>
        </Section>

        <Section title="7. Cookies e armazenamento no navegador">
          <p>O FasiTech pode usar armazenamento local do navegador para manter tokens e preferências de acesso a áreas protegidas. Esse recurso é técnico e não é utilizado para publicidade comportamental. Serviços de terceiros, como fontes e integrações externas, podem processar dados técnicos de conexão conforme suas próprias políticas.</p>
        </Section>

        <Section title="8. Atualizações desta política">
          <p>Esta política pode ser atualizada para refletir mudanças no portal, nos tratamentos realizados ou na legislação. A data de atualização será alterada nesta página. Para dúvidas, fale com a FASI pelo e-mail institucional.</p>
          <a href="mailto:fasicuntins@ufpa.br" className="inline-flex items-center gap-2 font-medium text-[#2563EB] hover:underline">
            <Mail className="h-4 w-4" aria-hidden /> fasicuntins@ufpa.br
          </a>
        </Section>
      </div>
    </PageShell>
  )
}
