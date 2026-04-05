/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#05060f",
          secondary: "#0b0d1a",
          card: "#0f1223",
        },
        accent: {
          purple: "#8B5CF6",
          blue: "#3B82F6",
          cyan: "#06B6D4",
          green: "#10B981",
          yellow: "#F59E0B",
          red: "#EF4444",
          pink: "#EC4899",
        },
        glass: "rgba(255,255,255,0.04)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        pulse2: "pulse2 2s cubic-bezier(0.4,0,0.6,1) infinite",
        shimmer: "shimmer 2s infinite",
        spin3d: "spin3d 20s linear infinite",
        orbit: "orbit 8s linear infinite",
        "glow-pulse": "glowPulse 3s ease-in-out infinite",
        "slide-up": "slideUp 0.5s cubic-bezier(0.16,1,0.3,1)",
        "fade-in": "fadeIn 0.4s ease",
        counter: "counter 0.8s ease-out",
      },
      keyframes: {
        float: {
          "0%,100%": { transform: "translateY(0px) rotate(0deg)" },
          "33%": { transform: "translateY(-20px) rotate(3deg)" },
          "66%": { transform: "translateY(-10px) rotate(-2deg)" },
        },
        pulse2: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        spin3d: {
          from: { transform: "rotateY(0deg) rotateX(15deg)" },
          to: { transform: "rotateY(360deg) rotateX(15deg)" },
        },
        orbit: {
          from: { transform: "rotate(0deg) translateX(120px) rotate(0deg)" },
          to: { transform: "rotate(360deg) translateX(120px) rotate(-360deg)" },
        },
        glowPulse: {
          "0%,100%": { boxShadow: "0 0 20px rgba(139,92,246,0.3)" },
          "50%": { boxShadow: "0 0 60px rgba(139,92,246,0.7), 0 0 100px rgba(59,130,246,0.3)" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(30px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      boxShadow: {
        glow: "0 0 30px rgba(139,92,246,0.4)",
        "glow-blue": "0 0 30px rgba(59,130,246,0.4)",
        "glow-cyan": "0 0 30px rgba(6,182,212,0.4)",
        "glow-green": "0 0 30px rgba(16,185,129,0.4)",
        card: "0 4px 24px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.06) inset",
        "card-hover": "0 8px 40px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.1) inset",
      },
    },
  },
  plugins: [],
};
