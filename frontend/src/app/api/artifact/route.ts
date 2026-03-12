import { FULL_HD } from "@/consts/displaySize";
import fs from "fs";
import markdownit from "markdown-it";
import highlightjs from "markdown-it-highlightjs";
import puppeteer, { LaunchOptions } from "puppeteer";

/**
 * Markdownコンテンツを含むHTMLテンプレートを生成する
 * @param elementString - 変換済みのMarkdownコンテンツ
 * @returns 完全なHTML文書
 */
const createHtmlWithMarkdown = (elementString: string) => {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css">
        <style>
          table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1em;
          }
          table, th, td {
            border: 1px solid #ddd;
          }
          th, td {
            padding: 8px;
            text-align: left;
          }
          th {
            background-color: #f2f2f2;
          }
        </style>
      </head>
      <body>
        ${elementString}
      </body>
    </html>
  `;
};

const executablePath = process.env.NEXT_PUBLIC_HOST_PUPPETEER_EXECUTABLE_PATH;
const puppeteerConfig: LaunchOptions = executablePath
  ? {
      executablePath,
      browser: "firefox",
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    }
  : {
      headless: true,
      browser: "firefox",
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    };

/**
 * MarkdownコンテンツをPDFに変換するAPIエンドポイント
 * @param request - POSTリクエストオブジェクト（mdContentを含むJSONボディ）
 * @returns PDFファイルのレスポンス
 */
export async function POST(request: Request) {
  const { mdContent } = await request.json();
  const mdElementString = markdownit().use(highlightjs).render(mdContent);
  const fullHtml = createHtmlWithMarkdown(mdElementString);
  const browser = await puppeteer.launch(puppeteerConfig);
  const page = await browser.newPage();
  await page.setViewport({ ...FULL_HD, deviceScaleFactor: 1 });
  await page.setContent(fullHtml);
  const tmpFilename = `${process.cwd()}/${Date.now()}.pdf`;
  await page.pdf({
    scale: 1,
    path: tmpFilename,
    format: "a4",
    printBackground: true,
    margin: {
      top: "1cm",
      right: "1cm",
      bottom: "1cm",
      left: "1cm",
    },
    preferCSSPageSize: true,
  });
  await browser.close();
  const pdfBuffer = fs.readFileSync(tmpFilename);
  fs.unlinkSync(tmpFilename);
  return new Response(pdfBuffer, {
    headers: {
      "Content-Type": "application/pdf",
      // ファイル名はClient側で指定するため、ここでは適当な固定値を設定
      "Content-Disposition": `attachment; filename=sample.pdf`,
    },
  });
}
