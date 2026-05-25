/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#070A12',
        panel: '#101623',
        line: 'rgba(255,255,255,0.12)',
        mint: '#6EE7B7',
        amber: '#F6C85F',
        coral: '#FF7A7A',
        cyan: '#67E8F9',
      },
      boxShadow: {
        glow: '0 24px 80px rgba(103, 232, 249, 0.16)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
