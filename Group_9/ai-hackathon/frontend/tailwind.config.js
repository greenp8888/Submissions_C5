export default {
    darkMode: ["class"],
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                border: "hsl(26 18% 82%)",
                input: "hsl(26 18% 82%)",
                ring: "hsl(18 62% 43%)",
                background: "hsl(40 38% 96%)",
                foreground: "hsl(215 24% 16%)",
                primary: {
                    DEFAULT: "hsl(18 62% 43%)",
                    foreground: "hsl(40 38% 98%)",
                },
                secondary: {
                    DEFAULT: "hsl(186 18% 88%)",
                    foreground: "hsl(215 24% 20%)",
                },
                muted: {
                    DEFAULT: "hsl(42 30% 91%)",
                    foreground: "hsl(215 16% 38%)",
                },
                accent: {
                    DEFAULT: "hsl(34 82% 70%)",
                    foreground: "hsl(215 24% 16%)",
                },
                card: {
                    DEFAULT: "hsla(40 38% 99% / 0.9)",
                    foreground: "hsl(215 24% 16%)",
                },
            },
            borderRadius: {
                xl: "1rem",
                "2xl": "1.5rem",
            },
            boxShadow: {
                panel: "0 20px 45px -30px rgba(41, 51, 65, 0.35)",
            },
            fontFamily: {
                heading: ["'Space Grotesk'", "sans-serif"],
                body: ["'Source Sans 3'", "sans-serif"],
            },
            backgroundImage: {
                "dashboard-grid": "linear-gradient(rgba(140, 126, 111, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140, 126, 111, 0.08) 1px, transparent 1px)",
            },
        },
    },
    plugins: [],
};
