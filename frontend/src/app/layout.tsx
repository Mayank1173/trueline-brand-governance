import type { Metadata } from "next";
import { IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import AppSidebar from "@/components/AppSidebar";
import AppHeader from "@/components/AppHeader";

const plex = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plex",
});

export const metadata: Metadata = {
  title: "Trueline",
  description: "Explainable brand governance before you publish.",
};

const themeInit = `try{var t=localStorage.getItem("theme");if(t==="light"||t==="dark"){document.documentElement.dataset.theme=t}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className={`${plex.variable} antialiased`}>
        <div className="flex min-h-screen flex-col md:flex-row">
          <AppSidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <AppHeader />
            <main className="flex-1 p-4 md:p-8">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}