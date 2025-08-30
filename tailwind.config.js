/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
       fontFamily: {
        poppins: ["Poppins", "sans-serif"],
      },
      colors: {
        'primary-blue': '#02025c',
        'secondary-blue': '#24d4fe',
        'primary-gray': '#f1eff9',
        'primary-purple': '#7c5af6'

      },
    },
  },
  plugins: [],
}
