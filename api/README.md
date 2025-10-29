# FasiTech API - Dados Sociais

API REST para consulta de dados sociais dos estudantes da FasiTech, construída com FastAPI e integrada ao Google Sheets.

## 🚀 Recursos

- **Consulta de dados sociais** com paginação e filtros avançados
- **Estatísticas agregadas** dos dados coletados
- **Autenticação via API Key** com suporte a Bearer token
- **Cache inteligente** para otimização de performance
- **Documentação automática** via Swagger/OpenAPI
- **Tratamento robusto de erros** e logging

## 📊 Endpoints Disponíveis

### Dados Sociais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/dados-sociais` | GET | Consulta dados sociais com filtros e paginação |
| `/api/v1/dados-sociais/estatisticas` | GET | Estatísticas agregadas dos dados |
| `/api/v1/dados-sociais/opcoes` | GET | Opções disponíveis para filtros |
| `/api/v1/dados-sociais/health` | GET | Verificação de saúde do serviço |

### Utilitários

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/dados-sociais/cache/clear` | POST | Limpa o cache do serviço |
| `/api/v1/dados-sociais/cache/info` | GET | Informações sobre o cache |
| `/health` | GET | Health check geral da API |

## 🔐 Autenticação

A API usa autenticação via API Key com suporte a dois formatos:

### Bearer Token (Recomendado)
```bash
curl -H "Authorization: Bearer sua_api_key" \
     "http://localhost:8000/api/v1/dados-sociais"
```

### Header X-API-Key
```bash
curl -H "X-API-Key: sua_api_key" \
     "http://localhost:8000/api/v1/dados-sociais"
```

### API Key de Exemplo
Para testes, use a API key pré-configurada:
```
fasitech_api_2024_social_data
```

## 🛠️ Instalação e Execução

### 1. Instalar Dependências
```bash
pip install fastapi uvicorn pandas google-api-python-client
```

### 2. Executar a API
```bash
# Desenvolvimento
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 3. Acessar Documentação
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📋 Exemplos de Uso

### Consulta Básica
```bash
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "http://localhost:8000/api/v1/dados-sociais?pagina=1&por_pagina=5"
```

### Consulta com Filtros
```bash
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "http://localhost:8000/api/v1/dados-sociais?cor_etnia=Pardo&trabalho=Sim&pagina=1"
```

### Estatísticas
```bash
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "http://localhost:8000/api/v1/dados-sociais/estatisticas"
```

### Opções de Filtros
```bash
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "http://localhost:8000/api/v1/dados-sociais/opcoes"
```

## 🔍 Filtros Disponíveis

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `periodo` | string | Período letivo | `2025.(3 e 4)` |
| `cor_etnia` | enum | Cor/etnia | `Branco`, `Pardo`, `Preto` |
| `pcd` | enum | Pessoa com deficiência | `Sim`, `Não` |
| `renda` | enum | Faixa de renda | `Até 1 salário mínimo` |
| `deslocamento` | enum | Meio de deslocamento | `Bicicleta/A pé`, `Ônibus` |
| `trabalho` | enum | Situação de trabalho | `Sim`, `Não` |
| `assistencia_estudantil` | enum | Qualidade da assistência | `Excelente`, `Boa`, `Regular` |
| `tipo_moradia` | enum | Tipo de moradia | `Própria`, `Alugada` |

## 📊 Estrutura da Response

### Dados Sociais (Paginados)
```json
{
  "dados": [
    {
      "matricula": "202316040005",
      "periodo": "2025.(3 e 4)",
      "cor_etnia": "Branco",
      "pcd": "Não",
      "renda": "Até 1 salário mínimo",
      "deslocamento": "Bicicleta/A pé",
      "trabalho": "Não",
      "assistencia_estudantil": "Regular",
      "saude_mental": "Sim, frequentemente",
      "data_hora": "2025-10-27T20:32:51"
    }
  ],
  "total": 49,
  "pagina": 1,
  "por_pagina": 20,
  "total_paginas": 3
}
```

### Estatísticas
```json
{
  "total_registros": 49,
  "distribuicao_cor_etnia": {
    "Pardo": 25,
    "Branco": 15,
    "Preto": 9
  },
  "percentual_pcd": 8.16,
  "percentual_trabalham": 32.65,
  "media_dispositivos": {
    "computadores": 1.2,
    "celulares": 2.1
  }
}
```

## 🛡️ Gerenciamento de API Keys

Use o script `api_manager.py` para gerenciar API keys:

```bash
# Gerar nova API key
python scripts/api_manager.py gerar "Nome do Cliente"

# Listar API keys válidas
python scripts/api_manager.py listar

# Testar API
python scripts/api_manager.py testar sua_api_key

# Ver exemplos
python scripts/api_manager.py exemplo
```

## 🎯 Cache e Performance

- **Cache automático**: Dados são armazenados em cache por 30 minutos
- **Cache inteligente**: Diferente por consulta e filtros
- **Gestão de cache**: Endpoints para limpar e monitorar o cache

## 🚨 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 401 | API key não fornecida ou inválida |
| 403 | Permissão insuficiente |
| 422 | Parâmetros de entrada inválidos |
| 500 | Erro interno do servidor |
| 503 | Serviço indisponível (problemas com Google Sheets) |

## 📝 Logs e Monitoramento

A API registra logs detalhados para:
- Autenticação de usuários
- Consultas realizadas
- Erros e exceções
- Performance do cache
- Acesso à planilha Google

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# API Keys adicionais (opcional)
export FASITECH_API_KEYS="key1:Cliente 1,key2:Cliente 2"

# Configurações do Google (herdam do Streamlit)
# - Credenciais já configuradas via .streamlit/secrets.toml
```

### Personalização

Para adicionar novas API keys permanentemente, edite o arquivo `src/middleware/auth.py`:

```python
VALID_API_KEYS = {
    "hash_da_sua_api_key": {
        "name": "Nome do Cliente",
        "permissions": ["read"]
    }
}
```

## 🤝 Integração

### Python
```python
import requests

headers = {"Authorization": "Bearer fasitech_api_2024_social_data"}
response = requests.get("http://localhost:8000/api/v1/dados-sociais", headers=headers)
dados = response.json()
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/dados-sociais', {
    headers: {
        'Authorization': 'Bearer fasitech_api_2024_social_data'
    }
});
const dados = await response.json();
```

### cURL
```bash
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "http://localhost:8000/api/v1/dados-sociais"
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte a documentação automática em `/docs`
2. Verifique os logs da aplicação
3. Use o endpoint `/api/v1/dados-sociais/health` para diagnosticar problemas
4. Entre em contato com a equipe de desenvolvimento

---

**Versão**: 1.0.0  
**Última atualização**: Outubro 2025