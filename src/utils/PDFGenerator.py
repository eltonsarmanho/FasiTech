from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import locale
from datetime import datetime


def _resolver_caminho_pdf(nome_arquivo):
    """Resolve o caminho adequado do PDF (usa /tmp no Lambda)."""
    if os.path.exists('/tmp'):
        return os.path.join('/tmp', nome_arquivo)
    return nome_arquivo


def _obter_fontes_padrao():
    """Retorna fontes normal e bold registradas com suporte a UTF-8."""
    fonte_normal = 'Helvetica'
    fonte_bold = 'Helvetica-Bold'

    try:
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/TTF/arial.ttf',
            '/System/Library/Fonts/Arial.ttf',
            'C\\Windows\\Fonts\\arial.ttf',
        ]

        font_bold_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/TTF/arialbd.ttf',
            '/System/Library/Fonts/Arial Bold.ttf',
            'C\\Windows\\Fonts\\arialbd.ttf',
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('UTF8-Regular', font_path))
                fonte_normal = 'UTF8-Regular'
                break

        for font_path in font_bold_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('UTF8-Bold', font_path))
                fonte_bold = 'UTF8-Bold'
                break

    except Exception as e:
        print(f"Aviso: Não foi possível carregar fontes UTF-8: {e}")

    return fonte_normal, fonte_bold

def gerar_pdf_projetos(resposta):
    """Gera um PDF contendo as informações do formulário de Projetos, ajustando o conteúdo conforme Natureza e Solicitação."""
    
    nome_arquivo = f"Parecer_{resposta[1].replace(' ', '_')}.pdf"
    caminho_pdf = _resolver_caminho_pdf(nome_arquivo)

    # Configuração do PDF
    largura, altura = A4
    margem_esquerda = 80
    margem_direita = largura - 80
    margem_superior = altura - 50  # Ajuste do topo
    largura_texto = margem_direita - margem_esquerda

    # Criar canvas com encoding UTF-8 e configuração de fontes melhorada
    c = canvas.Canvas(caminho_pdf, pagesize=A4)

    fonte_normal, fonte_bold = _obter_fontes_padrao()

    c.setFont(fonte_normal, 12)

    # Variáveis do formulário - garantir encoding correto
    docente = str(resposta[1]).encode('utf-8', 'replace').decode('utf-8')
    parecerista_1 = str(resposta[2]).encode('utf-8', 'replace').decode('utf-8')
    parecerista_2 = str(resposta[3]).encode('utf-8', 'replace').decode('utf-8')
    projeto = str(resposta[4]).encode('utf-8', 'replace').decode('utf-8')
    carga_horaria = str(resposta[5])
    edital = str(resposta[6]).encode('utf-8', 'replace').decode('utf-8')
    natureza = str(resposta[7]).encode('utf-8', 'replace').decode('utf-8')  # Pesquisa, Ensino ou Extensão
    ano_edital = str(resposta[8])
    solicitacao = str(resposta[9]).encode('utf-8', 'replace').decode('utf-8')  # Novo, Encerramento ou Renovação

    # Cabeçalho (centralizado)
    c.setFont(fonte_bold, 12)
    c.drawCentredString(largura / 2, margem_superior, "UNIVERSIDADE FEDERAL DO PARÁ")
    c.drawCentredString(largura / 2, margem_superior - 15, "CAMPUS UNIVERSITÁRIO DO TOCANTINS/CAMETÁ")
    c.drawCentredString(largura / 2, margem_superior - 30, "FACULDADE DE SISTEMAS DE INFORMAÇÃO - FASI")

    # Título do Parecer
    c.setFont(fonte_bold, 14)
    c.drawCentredString(largura / 2, margem_superior - 70, "PARECER")

    # Dados do Projeto
    c.setFont(fonte_normal, 12)
    y_pos = margem_superior - 100
    
    # Aplicar quebra de linha para o título do projeto
    titulo_texto = f"Título do Projeto: {projeto}"
    linhas_titulo = wrap_text(titulo_texto, largura_texto, c, fonte_normal)
    for linha in linhas_titulo:
        c.drawString(margem_esquerda, y_pos, linha)
        y_pos -= 20
    
    # Aplicar quebra de linha para o coordenador caso necessário
    coord_texto = f"Coordenador: {docente}"
    linhas_coord = wrap_text(coord_texto, largura_texto, c, fonte_normal)
    for linha in linhas_coord:
        c.drawString(margem_esquerda, y_pos, linha)
        y_pos -= 20

    # Corpo do parecer ajustado conforme natureza e solicitação
    parecer_texto = gerar_texto_parecer(natureza, solicitacao, docente, parecerista_1, parecerista_2, carga_horaria)

    # Escrever o texto do parecer com JUSTIFICAÇÃO
    y_pos -= 40
    c.setFont(fonte_normal, 12)
    y_pos = desenhar_texto_justificado(c, parecer_texto, margem_esquerda, y_pos, largura_texto, fonte_normal)

    # Data e Aprovação dos Pareceristas
    y_pos -= 40
    c.setFont(fonte_normal, 12)
    c.drawString(largura - 200, y_pos, f"Cametá, {obter_data_formatada()}.")

    y_pos -= 40
    c.drawString(margem_esquerda, y_pos, f"Aprovação do {parecerista_1}")
    y_pos -= 60
    c.drawString(margem_esquerda, y_pos, f"Aprovação do {parecerista_2}")

    c.save()
    return caminho_pdf  # Retorna o caminho do PDF gerado


def gerar_pdf_declaracao_projeto(resposta):
    """Gera um PDF de declaração para o formulário de Projetos."""

    docente = str(resposta[1]).encode('utf-8', 'replace').decode('utf-8')
    projeto = str(resposta[4]).encode('utf-8', 'replace').decode('utf-8')

    nome_arquivo = f"Declaracao_{projeto.replace(' ', '_')}.pdf"
    caminho_pdf = _resolver_caminho_pdf(nome_arquivo)

    largura, altura = A4
    margem_esquerda = 80
    margem_direita = largura - 80
    largura_texto = margem_direita - margem_esquerda

    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    fonte_normal, fonte_bold = _obter_fontes_padrao()

    # Cabeçalho
    y_pos = altura - 60
    c.setFont(fonte_bold, 12)
    cabecalho = [
        "SERVIÇO PÚBLICO FEDERAL",
        "UNIVERSIDADE FEDERAL DO PARÁ",
        "CAMPUS UNIVERSITÁRIO DO TOCANTINS/CAMETÁ",
        "FACULDADE DE SISTEMAS DE INFORMAÇÃO",
    ]
    for linha in cabecalho:
        c.drawCentredString(largura / 2, y_pos, linha)
        y_pos -= 15

    c.line(margem_esquerda, y_pos, margem_direita, y_pos)
    y_pos -= 40

    # Título
    c.setFont(fonte_bold, 14)
    c.drawCentredString(largura / 2, y_pos, "DECLARAÇÃO")
    y_pos -= 40

    # Corpo do texto
    c.setFont(fonte_normal, 12)
    texto_declaracao = (
        "A Direção da Faculdade de Sistemas de Informação declara que o Programa de Extensão "
        f"intitulado {projeto} sob a coordenação do professor {docente} está em consonância com as "
        "diretrizes do Projeto Pedagógico do Curso de Sistemas de Informação, assim como é relevante nas "
        "atividades desenvolvidas dentro dos eixos teóricos e práticos do referido curso."
    )

    y_pos = desenhar_texto_justificado(c, texto_declaracao, margem_esquerda, y_pos, largura_texto, fonte_normal)
    y_pos -= 40

    c.drawString(margem_esquerda, y_pos, "Atenciosamente,")
    y_pos -= 60

    c.drawRightString(margem_direita, y_pos, f"Cametá, {obter_data_extenso()}")
    y_pos -= 80

    c.setFont(fonte_bold, 10)
    c.drawCentredString(largura / 2, y_pos, "Prof. Dr. Elton Sarmanho Siqueira / Prof. Dr. Carlos dos Santos Portela")
    y_pos -= 15
    c.setFont(fonte_normal, 9)
    c.drawCentredString(largura / 2, y_pos, "Diretor da Faculdade de Sistemas de Informação / Vice-Diretor da Faculdade de Sistemas de Informação")
    y_pos -= 12
    c.drawCentredString(largura / 2, y_pos, "PORTARIA Nº 3686/2024 – REITORIA-UFPA / PORTARIA Nº 332/2024 – REITORIA-UFPA")
    y_pos -= 12
    c.drawCentredString(largura / 2, y_pos, "Trav. Padre Antônio Franco, 2617-Matinha")
    y_pos -= 12
    c.drawCentredString(largura / 2, y_pos, "Cametá-Pará- CEP:68400-000-Fone:3781-1182/1258")

    c.save()
    return caminho_pdf

def desenhar_texto_justificado(c, texto, x, y, largura_texto, fonte_normal):
    """Desenha um parágrafo de texto justificado no PDF, evitando palavras grudadas."""
    linhas = wrap_text(texto, largura_texto, c, fonte_normal)
    
    for i, linha in enumerate(linhas):
        palavras = linha.split()
        num_palavras = len(palavras)

        if i == len(linhas) - 1 or num_palavras == 1:
            # Última linha ou linha com uma única palavra → alinha à esquerda
            c.drawString(x, y, linha)
        else:
            # Justificação distribuindo espaços entre as palavras
            largura_linha = sum(c.stringWidth(palavra, fonte_normal, 12) for palavra in palavras)
            espaco_total = largura_texto - largura_linha  # Espaço restante na linha
            espaco_por_palavra = espaco_total / (num_palavras - 1)  # Espaço extra entre palavras

            x_temp = x
            for palavra in palavras[:-1]:
                c.drawString(x_temp, y, palavra)
                x_temp += c.stringWidth(palavra, fonte_normal, 12) + espaco_por_palavra + 1  # Adicionando 1px extra
            c.drawString(x_temp, y, palavras[-1])  # Última palavra na posição final
        
        y -= 20  # Espaçamento entre as linhas
    return y


def wrap_text(texto, largura_texto, c, fonte_normal):
    """Quebra o texto em linhas que cabem na largura especificada."""
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    
    for palavra in palavras:
        largura_linha = c.stringWidth(linha_atual + " " + palavra, fonte_normal, 12)
        if largura_linha <= largura_texto:
            linha_atual += " " + palavra
        else:
            linhas.append(linha_atual.strip())
            linha_atual = palavra
    
    if linha_atual:
        linhas.append(linha_atual.strip())

    return linhas

def gerar_texto_parecer(natureza, solicitacao, docente, parecerista_1, parecerista_2, carga_horaria):
    """Gera o texto do parecer conforme a Natureza e a Solicitação."""
    
    # Garantir encoding correto para todas as strings
    natureza = str(natureza).encode('utf-8', 'replace').decode('utf-8')
    solicitacao = str(solicitacao).encode('utf-8', 'replace').decode('utf-8')
    docente = str(docente).encode('utf-8', 'replace').decode('utf-8')
    parecerista_1 = str(parecerista_1).encode('utf-8', 'replace').decode('utf-8')
    parecerista_2 = str(parecerista_2).encode('utf-8', 'replace').decode('utf-8')
    
    parecer_base = f"A comissão de pareceristas composta pelos professores: {parecerista_1} e {parecerista_2} avaliou o projeto de {natureza.lower()} do professor {docente}."
    
    if solicitacao == "Novo":
        parecer_base += f" O projeto foi analisado quanto à sua relevância acadêmica e institucional, e após avaliação favorável, a comissão parecerista declara Parecer Favorável para sua realização com carga horária de {carga_horaria} horas."
        parecer_base += "\n\nO projeto proposto prevê atender os critérios exigidos na resolução vigente N. 4.918, DE 25 DE ABRIL DE 2017."

    elif solicitacao == "Encerramento":
        parecer_base += f" Após análise da documentação final e cumprimento dos objetivos estabelecidos, a comissão parecerista atesta o encerramento do projeto e aprova a finalização das atividades realizadas pelo docente."
        parecer_base += "\n\nO projeto atendeu aos diversos critérios exigidos na resolução vigente N. 4.918, DE 25 DE ABRIL DE 2017 e contribui significativamente para o desenvolvimento acadêmico e institucional."

    elif solicitacao == "Renovação":
        parecer_base += f" Com base na análise dos relatórios apresentados e no impacto positivo do projeto, a comissão parecerista aprova sua renovação, recomendando continuidade das ações previstas com carga horária de {carga_horaria} horas."
        parecer_base += "\n\nO projeto atendeu aos diversos critérios exigidos na resolução vigente N. 4.918, DE 25 DE ABRIL DE 2017 e contribui significativamente para o desenvolvimento acadêmico e institucional."

    
    return parecer_base

MESES_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def obter_data_extenso():
    """Retorna a data atual por extenso em português."""
    agora = datetime.now()
    mes = MESES_PT.get(agora.month, "")
    return f"{agora.day:02d} de {mes} de {agora.year}"


def obter_data_formatada():
    """Retorna a data atual formatada corretamente em português."""
    locale.setlocale(locale.LC_TIME, "C")
    return datetime.now().strftime("%d/%m/%Y")
