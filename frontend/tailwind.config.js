/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Warm paper stock for page + card surfaces.
        paper: {
          50: '#fdfcf8',
          100: '#f7f4ec',
          200: '#efeade',
          300: '#e3dbca',
          400: '#d2c7b0',
          500: '#b5a88d',
          600: '#97896d',
          700: '#7a6d54',
          800: '#635847',
          900: '#52493b',
          950: '#2c2721',
        },
        // Single quiet accent: olive. Used for links, active states and focus.
        accent: {
          50: '#f6f7ef',
          100: '#e9ecda',
          200: '#d3d9b6',
          300: '#b6c08a',
          400: '#97a45d',
          500: '#7d8b42',
          600: '#616e32',
          700: '#4a5527',
          800: '#3b4322',
          900: '#323a1e',
          950: '#191d0f',
        },
        // Risk-level palette (PRD §44), warmed to sit on paper.
        risk: {
          low: '#2f6b47',
          medium: '#8a6212',
          high: '#a4461d',
          critical: '#96231b',
        },
      },
      fontFamily: {
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        serif: ['Newsreader', 'Iowan Old Style', 'Georgia', 'Cambria', 'Times New Roman', 'serif'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        // Print-like: hairline rules carry the structure, shadows stay quiet.
        xs: '0 1px 1px 0 rgb(28 25 23 / 0.03)',
        soft: '0 1px 2px 0 rgb(28 25 23 / 0.04)',
        card: '0 1px 2px 0 rgb(28 25 23 / 0.04), 0 2px 8px -4px rgb(28 25 23 / 0.06)',
        lift: '0 8px 24px -14px rgb(28 25 23 / 0.20)',
      },
      backgroundImage: {
        'paper-fade':
          'radial-gradient(1000px 480px at 50% -12%, rgb(125 139 66 / 0.05), transparent 70%)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-in-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.98)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.25s ease-out both',
        'fade-in-up': 'fade-in-up 0.35s cubic-bezier(0.22, 1, 0.36, 1) both',
        'scale-in': 'scale-in 0.2s cubic-bezier(0.22, 1, 0.36, 1) both',
        shimmer: 'shimmer 1.6s infinite',
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
}
