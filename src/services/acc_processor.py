"""
Processador de Certificados ACC (Atividades Complementares de Curso)

Extrai cargas horárias de PDFs mesclados que podem conter:
- Certificados escaneados (imagens)
- PDFs nativos
- Documentos convertidos (.doc → PDF)
- Orientação paisagem ou retrato

Usa Groq Llama 3.3 70B + Vision para extrair e somar cargas horárias.
"""
import os
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise ImportError("python-dotenv not installed. Please install it with 'pip install python-dotenv'.") from exc

from agno.agent import Agent
from agno.models.google import Gemini

from agno.media import Image
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv(override=True)

if not os.getenv("GOOGLE_API_KEY"):
    raise EnvironmentError("GOOGLE_API_KEY not set. Please add it to your environment or .env file before running.")


def pdf_to_images(pdf_path: str, output_dir: str = "/tmp/acc_images") -> List[str]:
    """
    Converte cada página do PDF em imagem para processamento com Vision.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        output_dir: Diretório temporário para salvar imagens
    
    Returns:
        Lista com caminhos das imagens geradas
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("pdf2image not installed. Install with: pip install pdf2image pillow")
    
    # Criar diretório de saída
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📄 Convertendo PDF para imagens: {pdf_path}")
    
    # Converter PDF para imagens (alta resolução para OCR)
    images = convert_from_path(
        pdf_path,
        dpi=300,  # Alta resolução para melhor OCR
        fmt='png',
        thread_count=4
    )
    
    image_paths = []
    for i, image in enumerate(images, start=1):
        image_path = os.path.join(output_dir, f"page_{i:03d}.png")
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
        print(f"  ✓ Página {i}/{len(images)} convertida")
    
    return image_paths


def extrair_total_geral(texto: str) -> str:
    """
    Extrai a linha "TOTAL GERAL: X horas" do texto de resposta.
    
    Args:
        texto: Texto completo da resposta do agente
    
    Returns:
        String com o total geral ou mensagem de erro
    """
    import re
    
    # Padrões para capturar "TOTAL GERAL: X horas"
    padroes = [
        r'TOTAL GERAL:\s*(\d+(?:,\d+)?)\s*horas?',
        r'Total Geral:\s*(\d+(?:,\d+)?)\s*horas?',
        r'total geral:\s*(\d+(?:,\d+)?)\s*horas?',
        r'TOTAL:\s*(\d+(?:,\d+)?)\s*horas?',
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            horas = match.group(1).replace(',', '.')
            return f"TOTAL GERAL: {horas} horas"
    
    # Se não encontrar, tentar extrair a última linha com "horas"
    linhas = texto.strip().split('\n')
    for linha in reversed(linhas):
        if 'total' in linha.lower() and 'hora' in linha.lower():
            return linha.strip()
    
    return "⚠️  TOTAL GERAL não encontrado na resposta"


def criar_agente_extrator() -> Agent:
    """
    Cria um agente especializado em extrair cargas horárias de certificados.
    """
    INSTRUCOES = """Você é um especialista em extrair informações de certificados acadêmicos.

TAREFA:
1. Analise cada imagem de certificado fornecida
2. Extraia a CARGA HORÁRIA (em horas) de cada certificado
3. Identifique o nome/título da atividade quando possível
4. Retorne os dados em formato estruturado

FORMATOS COMUNS DE CARGA HORÁRIA:
- "40 horas"
- "40h"
- "Carga horária: 40h"
- "40 (quarenta) horas"
- "CH: 40h"

IMPORTANTE:
- Se não encontrar carga horária, retorne 0
- Ignore textos que não sejam carga horária (data, local, etc.)
- Converta sempre para número (ex: "40h" → 40)
- Se houver carga horária expressa por dia, converta para número, 8h por dia
- Se houver múltiplas cargas na mesma página, some todas

FORMATO DE RESPOSTA:
Para cada certificado, responda no formato:
```
PÁGINA X:
- Atividade: [nome da atividade]
- Carga Horária: [número] horas
```

Ao final, forneça:
```
TOTAL GERAL: [soma de todas as cargas] horas
```
"""

    agent = Agent(
        name="Extrator ACC",
        model=Gemini(id="gemini-2.5-flash"),
        instructions=INSTRUCOES,
        markdown=True,
        debug_mode=False
    )
    
    return agent


def salvar_resultado_txt(conteudo: str, matricula: str, nome: str, output_dir: str = "/tmp/acc_results") -> str:
    """
    Salva o resultado da análise em arquivo TXT.
    
    Args:
        conteudo: Conteúdo da análise
        matricula: Matrícula do aluno
        nome: Nome do aluno
        output_dir: Diretório para salvar o arquivo
    
    Returns:
        Caminho do arquivo TXT criado
    """
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Nome do arquivo: ACC_MATRICULA_DATA.txt
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ACC_{matricula}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Formatar conteúdo do arquivo
    cabecalho = f"""{'='*70}
ANÁLISE DE CERTIFICADOS ACC
{'='*70}

Aluno: {nome}
Matrícula: {matricula}
Data da Análise: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}

{'='*70}
RESULTADO DA ANÁLISE
{'='*70}

"""
    
    rodape = f"""

{'='*70}
Documento gerado automaticamente pelo Sistema de Automação da FASI
{'='*70}
"""
    
    conteudo_completo = cabecalho + conteudo + rodape
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo_completo)
    
    print(f"📄 Resultado salvo em: {filepath}")
    return filepath


def processar_certificados_acc(
    pdf_path: str,
    matricula: str = "DESCONHECIDA",
    nome: str = "Aluno"
) -> Dict[str, Any]:
    """
    Processa o PDF de certificados ACC e extrai cargas horárias.
    
    Args:
        pdf_path: Caminho para o PDF mesclado com certificados
        matricula: Matrícula do aluno
        nome: Nome do aluno
    
    Returns:
        Dicionário com resultados da extração incluindo caminho do TXT
    """
    print("\n" + "="*70)
    print("🎓 PROCESSADOR DE CERTIFICADOS ACC")
    print("="*70)
    print(f"📌 Aluno: {nome}")
    print(f"📌 Matrícula: {matricula}")
    
    # 1. Converter PDF para imagens
    image_paths = pdf_to_images(pdf_path)
    print(f"\n✓ Total de páginas convertidas: {len(image_paths)}")
    
    # 2. Criar agente extrator
    print("\n🤖 Inicializando agente de extração...")
    agent = criar_agente_extrator()
    
    # 3. Preparar imagens para o agente
    print("\n📊 Enviando certificados para análise...")
    images = [Image(filepath=img_path) for img_path in image_paths]
    
    # 4. Montar prompt com contexto
    prompt = f"""Analise os {len(images)} certificados anexados e extraia as cargas horárias.

Cada imagem representa uma página do documento ACC do aluno {nome} (Matrícula: {matricula}).
Processe todas as páginas e forneça o TOTAL GERAL ao final."""
    
    # 5. Processar com o agente
    print("\n⚙️  Processando certificados com Gemini...\n")
    print("-"*70)
    
    response = agent.run(
        input=prompt,
        images=images,
        stream=False
    )
    
    print("-"*70)
    print("\n✅ RESULTADO DA ANÁLISE:")
    print("="*70)
    print(response.content)
    print("="*70)
    
    # Extrair total geral do conteúdo
    total_geral = extrair_total_geral(response.content)
    
    print(f"\n🎯 {total_geral}")
    
    # 6. Salvar resultado em TXT
    print("\n💾 Salvando resultado em arquivo TXT...")
    txt_path = salvar_resultado_txt(response.content, matricula, nome)
    
    # 7. Limpar imagens temporárias
    print("\n🧹 Limpando imagens temporárias...")
    for img_path in image_paths:
        try:
            os.remove(img_path)
        except Exception as e:
            print(f"  ⚠️  Erro ao remover {img_path}: {e}")
    
    return {
        "total_paginas": len(image_paths),
        "resposta_completa": response.content,
        "total_geral": total_geral,
        "txt_path": txt_path,
        "matricula": matricula,
        "nome": nome,
        "status": "sucesso"
    }


# if __name__ == "__main__":
#     # Caminho para o PDF de certificados ACC
#     acc_pdf = os.path.join(
#         os.path.dirname(__file__),
#         "Arquivos",
#         "ACC2.pdf"
#     )
    
#     if not os.path.exists(acc_pdf):
#         print(f"❌ Erro: Arquivo não encontrado: {acc_pdf}")
#         exit(1)
    
#     # Processar certificados
#     resultado = processar_certificados_acc(acc_pdf)
    
#     print(f"\n✓ Processo concluído com sucesso!")
#     print(f"✓ Total de páginas processadas: {resultado['total_paginas']}")
#     print(f"✓ {resultado['total_geral']}")