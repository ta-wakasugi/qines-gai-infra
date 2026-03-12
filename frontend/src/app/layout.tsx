import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "QINeS GAI - Search",
  description: "GAIにサポートされたAUTOSAR関連ドキュメント検索アプリです",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        {/* グラデーション背景 */}
        <div className="relative bg-white flex flex-row justify-center w-full">
          <div className="relative bg-white w-full">
            <div className="relative flex h-full">
              <div className="absolute w-full h-screen top-0 left-0 overflow-hidden ">
                <div className="relative top-[-1229px] left-[-1332px]">
                  <div className="absolute w-[2858px] h-[2458px] top-[1024px] left-0 rounded-[1229px] [background:radial-gradient(50%_50%_at_50%_50%,rgba(49,62,58,0.4)_8%,rgba(150,167,175,0.1)_63%)]" />

                  <div className="absolute w-[2858px] h-[2458px] top-0 left-[1940px] rounded-[1229px] [background:radial-gradient(50%_50%_at_50%_50%,rgba(49,62,58,0.4)_8%,rgba(150,167,175,0.1)_83%)]" />
                </div>
                <div className="absolute w-full h-full top-[0px] left-[0px] bg-chat-area backdrop-blur-[28px] backdrop-brightness-[100%] [-webkit-backdrop-filter:blur(28px)_brightness(100%)]" />
              </div>
            </div>
          </div>
        </div>
        <main>{children}</main>
      </body>
    </html>
  );
}
