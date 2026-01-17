from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Identidade visual
LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _render_custom_styles():
    """Renderiza os estilos CSS customizados para a página."""
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stSidebar"],
            section[data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            [data-testid="stSidebarNav"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
                max-width: 0 !important;
            }
            .fasi-header {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 20px;
                padding: 32px;
                margin-bottom: 32px;
                color: #fff;
                box-shadow: 0 10px 40px rgba(26, 13, 46, 0.3);
                position: relative;
                overflow: hidden;
            }
            .fasi-header h1 {
                font-size: 2.1rem;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .fasi-header p {
                color: rgba(255,255,255,0.92);
                font-size: 1.08rem;
                line-height: 1.6;
                margin: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    """Função principal que renderiza a página de FAQ."""
    st.set_page_config(
        page_title="FAQ - FasiTech",
        layout="wide",
        page_icon="❓",
        initial_sidebar_state="collapsed",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )

    _render_custom_styles()

    # Logo
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width='stretch')

    # Header
    st.markdown(
        """
        <div class="fasi-header">
            <h1>❓ Perguntas Frequentes (FAQ)</h1>
            <p>Encontre respostas para as dúvidas mais comuns sobre matrículas, disciplinas,
            aproveitamento de estudos e outros processos acadêmicos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Seção 1: Dúvidas sobre Matrícula ---
    st.subheader("1. Dúvidas sobre Matrícula em Disciplinas")

    with st.expander("Qual disciplina devo me matricular?"):
        st.markdown("* Consulte o **calendário de ofertas do curso** disponível no site da Faculdade.")

    with st.expander("Quando será a oferta de uma determinada disciplina?"):
        st.markdown("* Consulte o **calendário de ofertas do curso** disponível no site da Faculdade.")

    with st.expander("Como solicitar aumento de créditos?"):
        st.markdown("* Entre em contato diretamente com o **Diretor ou Secretário** por e-mail ou mensagem.")

    with st.expander("O sistema não permite que eu faça determinadas disciplinas devido a conflito de horário. O que devo fazer?"):
        st.markdown("* Matricule-se em algumas disciplinas e deixe outras para o próximo período. Seja paciente, você não pode conquistar o mundo de uma vez.")

    with st.expander("Reprovei em uma disciplina no semestre passado. O que devo fazer?"):
        st.markdown("* Estude e espere a **próxima oferta da disciplina** em um turno diferente do seu. Você poderá cursar essa disciplina novamente quando ela for ofertada (consulte o quadro de ofertas no site do curso).")

    with st.expander("Me inscrevi em uma disciplina por engano que não faz parte da minha grade. O que devo fazer?"):
        st.markdown("* Retorne à tela de matrícula e **remova a disciplina indesejada**. Atenção na próxima vez!")

    with st.expander('Recebi a mensagem "NÃO É POSSÍVEL REALIZAR A MATRÍCULA PORQUE VOCÊ NÃO PREENCHEU A AVALIAÇÃO INSTITUCIONAL...". O que devo fazer?'):
        st.markdown('* Você deve **completar a Avaliação Institucional** antes de realizar a matrícula. Vá na aba de "Ensino", selecione a opção "Avaliação Institucional" e preencha a avaliação.')

    with st.expander("Nenhuma disciplina aparece no SIGAA. O que devo fazer?"):
        st.markdown("""
        * Adicione as disciplinas manualmente. Siga estes passos: "Adicionar Turma" $\\rightarrow$ "Adicionar disciplinas por código". Os códigos estão disponíveis na lista de ofertas da FASI.
        """)

    # --- Seção 2: Dúvidas sobre Disciplinas Específicas ---
    st.subheader("2. Dúvidas sobre Disciplinas Específicas (Estágio e TCC)")

    with st.expander("Como funcionam as disciplinas de Estágio I e II?"):
        st.markdown("""
        * Essas disciplinas estão no quadro de ofertas do curso (no site), mas **não são ofertadas diretamente no SIGAA**.
        * A direção, junto com a secretaria, realizará a matrícula durante o período definido no quadro de oferta.
        """)

    with st.expander("Há restrição para Atividades Flexibilizadas (Disciplinas)?"):
        st.markdown("* Sim. A reserva de vagas para as atividades flexibilizadas **não se aplica a disciplinas como TCC, estágios e práticas** que sejam regulamentadas por normas específicas. Nesses casos, o aluno deve seguir as regras de seu curso.")

    # --- Seção 3: Dúvidas sobre Atividades Flexibilizadas ---
    st.subheader("3. Dúvidas sobre Atividades Flexibilizadas (Aproveitamento de Estudos)")

    with st.expander("O aluno pode fazer disciplina (Atividade Flexibilizada) fora da UFPA? Se sim, como será computada no SIGAA?"):
        st.markdown("""
        * **Sim**, o aluno pode cursar disciplinas em outras Instituições de Ensino Superior (IES).
        * Para que as horas sejam validadas, a disciplina deve ser de uma área de conhecimento relevante para a sua formação.
        * A Unidade Acadêmica da UFPA ou da outra IES que ofertar a disciplina será a responsável por computar a carga horária.
        * A matrícula e o registro no SIGAA serão realizados de acordo com os procedimentos específicos definidos para o aproveitamento de estudos externos.
        """)

    with st.expander("O aluno pode fazer disciplina (Atividade Flexibilizada) na UFPA, mas fora do Campus de Cametá? Se sim, como ele deve solicitar no outro campus? Via SIGAA?"):
        st.markdown("""
        * **Sim**, é possível cursar disciplinas em outros campi da UFPA.
        * A matrícula nas atividades flexibilizadas dentro da UFPA será feita **diretamente pelo SIGAA**.
        * Os cursos de graduação da UFPA podem disponibilizar vagas de livre acesso em suas disciplinas, destinadas a alunos de cursos com essa modalidade de flexibilização.
        """)

    with st.expander("O aluno pode fazer quais tipos de disciplinas (Atividade Flexibilizada)? Existe alguma restrição?"):
        st.markdown("""
        * O aluno pode escolher as disciplinas de acordo com seus interesses e preferências.
        * **Restrição Principal:** A reserva de vagas para as atividades flexibilizadas não se aplica a disciplinas como TCC, estágios e práticas que sejam regulamentadas por normas específicas. Nesses casos, o aluno deve seguir as regras de seu curso.
        """)

    # --- Seção 4: Outorga de Grau e Diploma ---
    st.subheader("4. Informações sobre Outorga de Grau e Diploma")

    with st.expander("Como iniciar o processo de Outorga de Grau (ou Registro de Diploma)?"):
        st.markdown("""
        1.  Entre no **SIGAA**.
        2.  Localize menu "**Ensino**".
        3.  Localize opção "**Solicitação Validação de Documentos para Registro de Diploma**".
        4.  **Anexar os seguintes documentos:** Diploma de Ensino Médio, Carteira de Identidade e Declaração de Quitação da Biblioteca.
        """)

    # --- Seção 5: Acesso a Periódicos ---
    st.subheader("5. Acesso a Periódicos Científicos (CAPES)")

    with st.expander("Como posso acessar artigos e periódicos científicos usando meu login institucional da UFPA?"):
        st.markdown("""
        O acesso ao acervo de periódicos da CAPES é um benefício para toda a comunidade acadêmica da UFPA. Para utilizá-lo, siga o passo a passo para se autenticar com seu login institucional:

        1.  **Acesse o Portal de Periódicos da CAPES:**
            * Acesse o site oficial pelo link: **`https://www.periodicos.capes.gov.br/`**
        2.  **Clique em "ACESSO CAFE":**
            * No menu superior da página, localize e clique na opção **ACESSO CAFE**.
        3.  **Selecione a UFPA:**
            * Na tela da "Comunidade Acadêmica Federada", selecione **"UFPA"** na lista de instituições e clique no botão **"Enviar"**.
        4.  **Faça o Login Institucional:**
            * Você será redirecionado para a tela de autenticação da UFPA. Informe seu usuário e senha.
            * ***Atenção:*** O usuário deve ser o seu e-mail institucional completo (ex: `seulogin@ufpa.br` ou `seulogin@instituto.ufpa.br`).
        5.  **Acesso Concedido:**
            * Após o login, você terá acesso remoto a todas as bases de periódicos e artigos científicos assinados pela CAPES.

        #### Como buscar por uma base específica (Exemplo: IEEE Xplore)?
        Após realizar o login, se você deseja acessar uma base de dados específica, como a do IEEE, siga estes passos:
        1.  No menu do Portal, navegue até **Acervo $\\rightarrow$ Lista de bases e coleções**.
        2.  Na barra de busca, digite “**IEEE**” e clique em “**Enviar**”.
        3.  Nos resultados, clique sobre o nome da base (ex: **IEEE Xplore Digital Library**).
        4.  Na página seguinte, clique no link para acessar a base.
        """)
    # Botão voltar ao menu principal
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 Voltar ao Menu Principal", use_container_width=True):
            st.switch_page("main.py")

if __name__ == "__main__":
    main()