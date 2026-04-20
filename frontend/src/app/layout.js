import "./globals.css";

export const metadata = {
  title: "Adaptive Training AI — Prescrição Inteligente de Treino",
  description:
    "Plataforma de prescrição adaptativa de treinamento físico baseada em inteligência artificial. Monitore performance, registre sessões e receba microciclos personalizados.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
