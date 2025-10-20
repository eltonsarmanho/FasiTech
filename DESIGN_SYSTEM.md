# Identidade Visual - FasiTech Forms Platform

## Paleta de Cores

### Cores Primárias
- **Roxo Escuro Institucional**: `#1a0d2e` - Cabeçalhos e textos principais
- **Roxo Médio**: `#2d1650` - Gradientes intermediários
- **Roxo Vibrante**: `#4a1d7a` - Base dos gradientes e destaques
- **Roxo Claro**: `#7c3aed` - Elementos interativos e botões

### Cores Secundárias
- **Branco**: `#ffffff` - Fundo principal e cards
- **Cinza Claro**: `#f8fafc` - Backgrounds alternativos
- **Cinza Médio**: `#64748b` - Textos secundários
- **Cinza Borda**: `#e2e8f0` - Bordas e separadores

### Cores de Destaque
- **Amarelo Ouro**: `#fbbf24` - Alertas importantes
- **Vermelho**: `#dc2626` - Campos obrigatórios e erros

## Gradientes

### Gradiente Principal (Hero Sections)
```css
background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
```

### Gradiente Botões
```css
background: linear-gradient(135deg, #4a1d7a 0%, #7c3aed 100%);
```

### Gradiente Hover (Botões)
```css
background: linear-gradient(135deg, #5a2d8a 0%, #8c4afd 100%);
```

## Tipografia

- **Fonte**: Sans Serif (padrão do sistema)
- **Títulos Principais**: 1.9rem - 2.2rem, weight: 700
- **Subtítulos**: 1.5rem, weight: 600
- **Texto Corpo**: 0.95rem - 1rem, line-height: 1.6-1.8
- **Botões**: 1rem, weight: 600, uppercase, letter-spacing: 0.5px

## Componentes

### Cards
- Border-radius: 16px
- Padding: 36px
- Box-shadow: `0 4px 16px rgba(0, 0, 0, 0.06)`
- Border: `1px solid #e2e8f0`
- Hover: Transform `translateY(-4px)` + shadow intensificada

### Botões
- Border-radius: 12px
- Padding: 16px 32px
- Box-shadow: `0 4px 12px rgba(74, 29, 122, 0.25)`
- Hover: Transform `translateY(-2px)` + shadow `0 8px 24px`
- Transição: all 0.3s ease

### Logo Container
- Background: #ffffff
- Border-radius: 12px
- Box-shadow: `0 4px 12px rgba(0, 0, 0, 0.08)`
- Padding: 16px

### Hero Sections
- Border-radius: 16px
- Padding: 36px
- Box-shadow: `0 10px 30px rgba(26, 13, 46, 0.25)`
- Efeito radial de luz no canto superior direito

## Animações

### Float (ícones)
```css
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}
animation: float 3s ease-in-out infinite;
```

### Hover States
- Transform: translateY(-2px to -4px)
- Transition: 0.3s ease
- Box-shadow ampliada

## Princípios de Design

1. **Consistência**: Todos os formulários seguem a mesma estrutura visual
2. **Hierarquia**: Uso de tamanhos, pesos e cores para guiar o olhar
3. **Espaçamento**: Generoso uso de whitespace para respiração visual
4. **Acessibilidade**: Contraste adequado entre texto e background
5. **Responsividade**: Layout adaptativo com colunas flexíveis
6. **Feedback Visual**: Animações suaves em interações

## Aplicação

A identidade visual está implementada em:
- `/src/app/main.py` - Página principal
- `/src/app/pages/FormACC.py` - Formulário ACC
- `/src/app/pages/formulario2.py` - Outros formulários
- `/.streamlit/config.toml` - Configurações de tema

Todos os estilos CSS estão inline nos componentes para facilitar manutenção e garantir consistência.
