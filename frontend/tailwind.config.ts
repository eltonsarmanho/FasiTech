import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      colors: {
        // ── FASI Brand (azul puro da logo — referência, não usar como UI) ──
        fasi: {
          50:  '#ebebff',
          100: '#d1d1ff',
          200: '#a8a8ff',
          300: '#7070ff',
          400: '#3d3dff',
          500: '#0000ff',
          600: '#0000d6',
          700: '#0000a8',
          800: '#000080',
          900: '#00005a',
          950: '#000033',
        },
        // ── Navy — azul institucional (primary da UI) ──────────────────────
        navy: {
          DEFAULT: '#1A3A6B',
          light:   '#2A4A7B',
          dark:    '#112B54',
        },
        // ── Royal — azul interativo (CTAs, focus rings, links) ─────────────
        royal: {
          DEFAULT: '#2563EB',
          dark:    '#1d4ed8',
          light:   '#3b82f6',
        },
        // ── Sistema semântico (tokens) ─────────────────────────────────────
        border:      'hsl(var(--border))',
        input:       'hsl(var(--input))',
        ring:        'hsl(var(--ring))',
        background:  'hsl(var(--background))',
        foreground:  'hsl(var(--foreground))',
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT:    'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        card: {
          DEFAULT:    'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'navy-sm': '0 1px 3px rgba(26,58,107,0.08), 0 1px 2px rgba(26,58,107,0.04)',
        'navy-md': '0 4px 14px rgba(26,58,107,0.12), 0 2px 6px rgba(26,58,107,0.06)',
        'navy-lg': '0 8px 28px rgba(26,58,107,0.16), 0 4px 10px rgba(26,58,107,0.08)',
        // mantidos para compatibilidade
        'fasi-sm': '0 1px 3px 0 rgba(0,0,255,0.06), 0 1px 2px -1px rgba(0,0,255,0.04)',
        'fasi-md': '0 4px 12px -1px rgba(0,0,255,0.08), 0 2px 6px -2px rgba(0,0,255,0.05)',
        'fasi-lg': '0 8px 24px -3px rgba(0,0,255,0.10), 0 4px 10px -4px rgba(0,0,255,0.06)',
        'fasi-xl': '0 20px 40px -5px rgba(0,0,255,0.12), 0 8px 16px -6px rgba(0,0,255,0.06)',
      },
      animation: {
        'fade-in':  'fadeIn 0.25s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' },                               to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}

export default config
