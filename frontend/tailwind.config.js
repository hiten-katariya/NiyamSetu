/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        niyam: {
          bg: '#F6F8FB',
          surface: '#FFFFFF',
          'surface-alt': '#EEF2F7',
          border: '#DDE3EC',
          text: '#1B2433',
          'text-muted': '#5A6678',
          primary: '#1F4E8C',
          'primary-hover': '#173D70',
          'primary-tint': '#E6EEF8',
          focus: '#2B6CD4',
          // Status colors
          'status-success': '#1E6B3A',
          'status-success-bg': '#E5F4EA',
          'status-warning': '#8A5A00',
          'status-warning-bg': '#FFF3D6',
          'status-danger': '#B42318',
          'status-danger-bg': '#FDE8E6',
          'status-neutral': '#4B5565',
          'status-neutral-bg': '#EDEFF3',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
