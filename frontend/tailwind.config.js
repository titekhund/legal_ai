/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563eb', // Blue
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#1e293b',
        },
        accent: {
          DEFAULT: '#f59e0b', // Amber (for citations)
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        background: '#f9fafb', // Light gray
        text: {
          DEFAULT: '#1f2937', // Dark gray
          light: '#6b7280',
          lighter: '#9ca3af',
        }
      },
      fontFamily: {
        sans: ['var(--font-noto-sans-georgian)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
