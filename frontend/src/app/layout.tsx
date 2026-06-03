import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "996 AI Asset Studio",
  description: "Asset workflow studio for 996 art production.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

