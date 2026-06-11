import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#070B14',
        panel: '#0E1628',
        panelAlt: '#111C33',
        line: '#23314E',
        text: '#E8EEF9',
        muted: '#90A0BC',
        accent: '#70E1FF',
        accent2: '#A78BFA',
        success: '#4ADE80',
        danger: '#FB7185',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(112, 225, 255, 0.15), 0 24px 80px rgba(4, 10, 24, 0.5)',
      },
      backgroundImage: {
        mesh:
          'radial-gradient(circle at 20% 20%, rgba(112,225,255,0.10), transparent 28%), radial-gradient(circle at 80% 0%, rgba(167,139,250,0.10), transparent 24%), linear-gradient(180deg, #060A12 0%, #0A1220 100%)',
      },
    },
  },
  plugins: [],
} satisfies Config
