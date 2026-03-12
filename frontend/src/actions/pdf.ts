"use server";
import { pdfjs } from "react-pdf";
pdfjs.GlobalWorkerOptions.workerSrc = require.resolve(
  "pdfjs-dist/build/pdf.worker.min.js"
);

/**
 * 指定されたパスからPDFファイルを取得し、Base64文字列に変換します
 * @param path - PDFファイルのURLパス
 * @returns Promise<string> - PDFファイルのBase64エンコードされた文字列
 * @todo 設定可能なドメインやS3ストレージからの取得に更新する必要があります
 */
export const getBase64Pdf = async (path: string) => {
  const r = await fetch(path);
  const data = new Uint8Array(await r.arrayBuffer());
  const base64 = Buffer.from(data).toString("base64");
  return base64;
};
