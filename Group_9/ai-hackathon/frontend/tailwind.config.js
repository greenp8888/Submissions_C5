export default {
    darkMode: ["class"],
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                border: "hsl(214 24% 86%)",
                input: "hsl(214 24% 86%)",
                ring: "hsl(174 67% 40%)",
                background: "hsl(210 40% 98%)",
                foreground: "hsl(222 47% 11%)",
                primary: {
                    DEFAULT: "hsl(173 70% 38%)",
                    foreground: "hsl(0 0% 100%)",
                },
                secondary: {
                    DEFAULT: "hsl(210 40% 96%)",
                    foreground: "hsl(222 47% 11%)",
                },
                muted: {
                    DEFAULT: "hsl(210 40% 96%)",
                    foreground: "hsl(215 16% 47%)",
                },
                accent: {
                    DEFAULT: "hsl(28 92% 58%)",
                    foreground: "hsl(210 40% 98%)",
                },
                card: {
                    DEFAULT: "hsla(0 0% 100% / 0.92)",
                    foreground: "hsl(222 47% 11%)",
                },
            },
            borderRadius: {
                xl: "1rem",
                "2xl": "1.5rem",
            },
            boxShadow: {
                panel: "0 24px 60px -34px rgba(15, 23, 42, 0.18)",
            },
            fontFamily: {
                heading: ["'Space Grotesk'", "sans-serif"],
                body: ["'Source Sans 3'", "sans-serif"],
            },
            backgroundImage: {
                "dashboard-grid": "linear-gradient(rgba(148, 163, 184, 0.18) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.18) 1px, transparent 1px)",
            },
        },
    },
    plugins: [],
};
