import type { Metadata } from "next";
import { Instrument_Serif, DM_Mono, Inter } from "next/font/google";
import { AppThemeProvider } from "@/lib/appTheme";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  weight: ["400"],
  variable: "--font-serif",
  subsets: ["latin"],
});

const dmMono = DM_Mono({
  weight: ["400", "500"],
  variable: "--font-mono",
  subsets: ["latin"],
});

const inter = Inter({
  weight: ["400", "500", "700", "800", "900"],
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SignalForge — Product Idea Analyzer",
  description: "Competitive intelligence from 6 sources in 30 seconds",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${instrumentSerif.variable} ${dmMono.variable} ${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <AppThemeProvider>{children}</AppThemeProvider>
      </body>
    </html>
  );
}
