module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#0A0E27',
        'secondary': '#1A1F3A',
        'accent': '#00D9FF',
        'accent-light': '#00F0FF',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'wave': 'wave 0.6s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(0, 217, 255, 0.8)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 40px rgba(0, 217, 255, 0.4)' },
        },
        'wave': {
          '0%, 100%': { height: '20px' },
          '50%': { height: '50px' },
        }
      }
    },
  },
  plugins: [],
}
