"""
Processador de Certificados ACC (Atividades Complementares de Curso)

Extrai cargas horárias de PDFs mesclados que podem conter:
- Certificados escaneados (imagens)
- PDFs nativos
- Documentos convertidos (.doc → PDF)
- Orientação paisagem ou retrato

"""
import os
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise ImportError("python-dotenv not installed. Please install it with 'pip install python-dotenv'.") from exc

from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import Image, File
from pathlib import Path

from backend.config.LLMConfig import GEMINI_MODEL_VISION as GEMINI_MODEL

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
    print(f"📄 Convertendo PDF para imagens: {pdf_path}")
    
    # Verificar se o arquivo existe
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")
    
    # Verificar se é um arquivo PDF válido
    file_size = os.path.getsize(pdf_path)
    print(f"   Tamanho do arquivo: {file_size / 1024:.2f} KB")
    
    if file_size == 0:
        raise ValueError("Arquivo PDF está vazio")
    
    try:
        from pdf2image import convert_from_path
        print("   ✓ pdf2image importado com sucesso")
    except ImportError as e:
        raise ImportError(f"pdf2image não disponível. Instale com: pip install pdf2image pillow. Erro: {e}")
    
    # Verificar se poppler está disponível
    import shutil
    if not shutil.which("pdftoppm"):
        raise RuntimeError(
            "poppler-utils não encontrado. Instale com:\n"
            "  Ubuntu/Debian: sudo apt-get install poppler-utils\n"
            "  CentOS/RHEL: sudo yum install poppler-utils\n"
            "  macOS: brew install poppler"
        )
    print("   ✓ poppler-utils encontrado")
    
    # Criar diretório de saída
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"   ✓ Diretório criado: {output_dir}")
    except Exception as e:
        raise OSError(f"Não foi possível criar diretório {output_dir}: {e}")
    
    try:
        # Converter PDF para imagens (alta resolução para OCR)
        print("   🔄 Iniciando conversão...")
        images = convert_from_path(
            pdf_path,
            dpi=300,  # Alta resolução para melhor OCR
            fmt='png',
            thread_count=2  # Reduzir para evitar problemas de memória no servidor
        )
        print(f"   ✓ PDF convertido: {len(images)} páginas")
        
    except Exception as e:
        raise RuntimeError(f"Erro ao converter PDF: {e}")
    
    if not images:
        raise ValueError("PDF não contém páginas válidas para conversão")
    
    image_paths = []
    for i, image in enumerate(images, start=1):
        try:
            image_path = os.path.join(output_dir, f"page_{i:03d}.png")
            image.save(image_path, 'PNG')
            
            # Verificar se a imagem foi salva corretamente
            if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                image_paths.append(image_path)
                print(f"  ✓ Página {i}/{len(images)} convertida ({os.path.getsize(image_path) / 1024:.1f} KB)")
            else:
                print(f"  ⚠️ Erro ao salvar página {i}: arquivo vazio ou não criado")
                
        except Exception as e:
            print(f"  ⚠️ Erro ao processar página {i}: {e}")
    
    if not image_paths:
        raise RuntimeError("Nenhuma página foi convertida com sucesso")
    
    print(f"   ✅ Conversão concluída: {len(image_paths)} imagens geradas")
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
    Cria um agente Gemini especializado em extrair cargas horárias de certificados ACC.
    """
    INSTRUCOES = """Você é um especialista em extrair informações de certificados acadêmicos.

TAREFA:
1. Analise cada certificado PDF fornecido
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

    try:
        print(f"   🤖 Criando agente Gemini ({GEMINI_MODEL})...")
        agent = Agent(
            name="Extrator ACC",
            model=Gemini(id=GEMINI_MODEL),
            instructions=INSTRUCOES,
            markdown=True,
            debug_mode=False,
        )
        print("   ✓ Agente Gemini configurado com sucesso")
        return agent

    except Exception as e:
        print(f"   ❌ Erro ao criar agente: {e}")
        raise RuntimeError(f"Falha ao inicializar agente Gemini: {e}")


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
    print(f"📌 Arquivo PDF: {pdf_path}")
    print(f"📌 Tamanho do arquivo: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    
    try:
        # Verificar dependências críticas
        print("\n🔍 Verificando dependências...")
        
        # Verificar GOOGLE_API_KEY
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY não configurada")
        print(f"✓ GOOGLE_API_KEY configurada (primeiros 10 chars: {api_key[:10]}...)")
        
        # Verificar pdf2image
        try:
            from pdf2image import convert_from_path
            print("✓ pdf2image disponível")
        except ImportError as e:
            raise ImportError(f"pdf2image não disponível: {e}")
        
        # Verificar agno/Gemini
        try:
            from agno.models.google import Gemini
            print("✓ agno/Gemini disponível")
        except ImportError as e:
            raise ImportError(f"agno não disponível: {e}")
        
        # 1. Criar agente extrator
        print("\n🤖 Inicializando agente de extração...")
        agent = criar_agente_extrator()
        print(f"✓ Agente criado com sucesso (modelo: {GEMINI_MODEL})")

        # 2. Montar prompt com contexto
        prompt = f"""Analise o documento PDF de certificados ACC anexado e extraia as cargas horárias.

O arquivo contém certificados do aluno {nome} (Matrícula: {matricula}).
Processe todas as páginas do PDF e forneça o TOTAL GERAL ao final."""

        # 3. Processar com o agente (PDF direto)
        print(f"\n⚙️  Processando certificados com Gemini ({GEMINI_MODEL})...\n")
        print("-"*70)
        
        # Criar objeto File para o agente
        pdf_file = File(filepath=pdf_path)
        
        # Enviar PDF diretamente (ambos modelos suportam)
        response = agent.run(
            input=prompt,
            files=[pdf_file],
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
        
        return {
            "total_paginas": 1,  # PDF processado diretamente
            "resposta_completa": response.content,
            "total_geral": total_geral,
            "txt_path": txt_path,
            "matricula": matricula,
            "nome": nome,
            "status": "sucesso"
        }
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO no processamento ACC:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        
        # Retornar resultado de erro
        return {
            "total_paginas": 0,
            "resposta_completa": f"ERRO: {str(e)}",
            "total_geral": "⚠️ ERRO no processamento",
            "txt_path": None,
            "matricula": matricula,
            "nome": nome,
            "status": "erro",
            "erro": str(e),
            "tipo_erro": type(e).__name__
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