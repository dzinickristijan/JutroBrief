import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";

const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-serif" });
const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Jutarnji brief",
  description: "Sve što je bitno iz Hrvatske i svijeta — u 5 minuta, svako jutro.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hr">
      <body className={`${fraunces.variable} ${inter.variable} font-sans antialiased`}>
        <div className="site-shell">
          <Header />
          {children}
          <footer className="site-footer">
            Sažeci pisani vlastitim riječima, uz linkove na izvore.
          </footer>
        </div>
      </body>
    </html>
  );
}
