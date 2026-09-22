/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f8f9fa",
          100: "#e6f9ed",
          500: "#2c3e50",
          600: "#1b5e20",
        },
        brand: {
          DEFAULT: "#5b0428",
          hover: "#7b0538",
          accent: "#DB1A1A",
        },
        success: {
          50: "#e6f9ed",
          500: "#1b5e20",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
