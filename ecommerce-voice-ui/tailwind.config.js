/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}"
  ],
 theme: {
  extend: {
    animation: {
      wave: "wave 1.2s ease-in-out infinite",
      fadeInUp: "fadeInUp 0.3s ease-out",
    },
    keyframes: {
      wave: {
        "0%, 100%": { height: "6px" },
        "50%": { height: "20px" },
      },
      fadeInUp: {
        "0%": { opacity: 0, transform: "translateY(6px)" },
        "100%": { opacity: 1, transform: "translateY(0)" },
      },
    },
  },
},
  plugins: [],
}
