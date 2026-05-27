import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "西湖即时路线 Agent",
  description: "面向杭州西湖周边现在就出发场景的 AI 本地路线决策产品原型",
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
