import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Argentier — ton vrai run-rate, pas ton relevé",
  description:
    "Agent d'optimisation bancaire et fiscale pour TPE, freelances et EI, branché sur Qonto.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
