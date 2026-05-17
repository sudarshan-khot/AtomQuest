export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  safelist: [
    'lg:ml-16', 'lg:ml-60',
    'btn-sm', 'btn-md', 'btn-lg',
    'bg-primary-50', 'bg-primary-100', 'text-primary-700',
    'border-primary-200', 'text-primary-600',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Acid Lime accent — 10%
        primary: {
          DEFAULT: '#A3E635',
          50:  '#f7fee7',
          100: '#ecfccb',
          200: '#d9f99d',
          300: '#bef264',
          400: '#a3e635',
          500: '#A3E635',
          600: '#84cc16',
          700: '#65a30d',
          800: '#4d7c0f',
          900: '#365314',
        },
        // Dark Graphite — 30%
        graphite: {
          DEFAULT: '#24292E',
          50:  '#f6f8fa',
          100: '#eaeef2',
          200: '#d0d7de',
          300: '#afb8c1',
          400: '#8c959f',
          500: '#6e7781',
          600: '#57606a',
          700: '#424a53',
          800: '#32383f',
          900: '#24292E',
          950: '#1c2128',
        },
        // Off-White / Cream — 60%
        cream: {
          DEFAULT: '#F7F7F5',
          50:  '#fefefe',
          100: '#F7F7F5',
          200: '#efefec',
          300: '#e4e4e0',
          400: '#d1d1cc',
          500: '#b8b8b2',
          600: '#9a9a93',
          700: '#7a7a73',
          800: '#5c5c56',
          900: '#3d3d39',
        },
      },
      animation: {
        'fade-in':  'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: '0' },                              '100%': { opacity: '1' } },
        slideIn: { '0%': { transform: 'translateX(100%)' },             '100%': { transform: 'translateX(0)' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
      },
    },
  },
  plugins: [],
}
