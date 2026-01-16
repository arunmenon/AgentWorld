/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Dark theme color palette
        background: {
          DEFAULT: '#0f0f0f',
          secondary: '#1a1a1a',
          tertiary: '#242424',
        },
        foreground: {
          DEFAULT: '#fafafa',
          secondary: '#a1a1a1',
          muted: '#6b6b6b',
        },
        primary: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
          active: '#4f46e5',
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#27272a',
          hover: '#3f3f46',
          foreground: '#fafafa',
        },
        accent: {
          DEFAULT: '#22d3ee',
          hover: '#67e8f9',
          foreground: '#0f0f0f',
        },
        success: {
          DEFAULT: '#22c55e',
          hover: '#4ade80',
          background: '#052e16',
          foreground: '#dcfce7',
        },
        warning: {
          DEFAULT: '#f59e0b',
          hover: '#fbbf24',
          background: '#451a03',
          foreground: '#fef3c7',
        },
        error: {
          DEFAULT: '#ef4444',
          hover: '#f87171',
          background: '#450a0a',
          foreground: '#fecaca',
        },
        border: {
          DEFAULT: '#27272a',
          hover: '#3f3f46',
        },
        // Agent state colors
        agent: {
          idle: '#6b7280',
          thinking: '#f59e0b',
          speaking: '#22c55e',
          listening: '#6366f1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-slow': 'bounce 2s infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
}
