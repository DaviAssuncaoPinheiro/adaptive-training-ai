import "./globals.css";
import { Instrument_Serif, Inter_Tight, JetBrains_Mono } from "next/font/google";

const displayFont = Instrument_Serif({
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-display-next",
});

const bodyFont = Inter_Tight({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-body-next",
});

const monoFont = JetBrains_Mono({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-mono-next",
});

export const metadata = {
  title: "Adaptive Training AI - Prescricao Inteligente de Treino",
  description:
    "Plataforma de prescricao adaptativa de treinamento fisico baseada em inteligencia artificial. Monitore performance, registre sessoes e receba microciclos personalizados.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="pt-BR"
      className={`${displayFont.variable} ${bodyFont.variable} ${monoFont.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
