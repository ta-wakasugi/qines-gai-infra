import { getBase64Pdf } from "@/actions/pdf";
import { ContextType } from "@/models/conversation";
import { DocumentType } from "@/models/document";
import { atom, useAtom } from "jotai";

const DOCUMENT_ORIGIN =
  process.env.NEXT_PUBLIC_DOCUMENT_ORIGIN || "http://host.docker.internal:3000";

const numPagesAtom = atom(0);
const scaleAtom = atom(1);
const pdfTitleAtom = atom<string | null>(null);
const base64PdfAtom = atom<string | null>(null);
const initialPageIndexAtom = atom(0);

/**
 * PDFビューアーの状態を管理するカスタムフック
 * @returns {Object} PDFビューアーの状態と操作関数を含むオブジェクト
 * @property {string | null} pdfTitle - PDFファイルのタイトル
 * @property {Function} setPdfTitle - PDFタイトルを設定する関数
 * @property {string | null} base64Pdf - Base64エンコードされたPDFデータ
 * @property {Function} resetPdf - PDFの状態をリセットする関数
 * @property {Function} fetchBase64Pdf - PDFファイルを取得し初期ページをリセットする関数
 * @property {number} numPages - PDFの総ページ数
 * @property {Function} setNumPages - 総ページ数を設定する関数
 * @property {number} scale - PDFの表示倍率
 * @property {Function} zoomIn - PDFを拡大する関数
 * @property {Function} zoomOut - PDFを縮小する関数
 * @property {number} initialPageIndex - 初期表示ページのインデックス
 * @property {Function} fetchBase64PdfWithSpecificPage - 特定ページを指定してPDFを取得する関数
 * @property {Function} resetInitialPageIndex - 初期ページをリセットする関数
 */
export const usePdf = () => {
  const [numPages, setNumPages] = useAtom(numPagesAtom);
  const [scale, setScale] = useAtom(scaleAtom);
  const [pdfTitle, setPdfTitle] = useAtom(pdfTitleAtom);
  const [base64Pdf, setBase64Pdf] = useAtom(base64PdfAtom);
  const [initialPageIndex, setInitialPageIndex] = useAtom(initialPageIndexAtom);
  const resetInitialPageIndex = () => setInitialPageIndex(0);

  /**
   * PDFファイルを取得し、Base64形式で保存する
   * @param document - 取得対象のドキュメントまたはコンテキスト
   */
  const fetchPdf = async (document: DocumentType | ContextType) => {
    setPdfTitle(document.title);
    const path = DOCUMENT_ORIGIN + document.path;
    const base64Pdf = await getBase64Pdf(path);
    setBase64Pdf(base64Pdf);
  };

  /**
   * PDFファイルをBase64形式で取得し、初期ページをリセットする
   * @param document - 取得対象のドキュメントまたはコンテキスト
   */
  const fetchBase64Pdf = async (document: DocumentType | ContextType) => {
    await fetchPdf(document);
    resetInitialPageIndex();
  };

  /**
   * 特定のページを指定してPDFファイルを取得する
   * @param document - 取得対象のドキュメントまたはコンテキスト
   * @param pageIndex - 表示するページ番号
   */
  const fetchBase64PdfWithSpecificPage = async (
    document: DocumentType | ContextType,
    pageIndex: number
  ) => {
    await fetchPdf(document);
    setInitialPageIndex(pageIndex);
  };

  /**
   * PDFビューアーの状態をリセットする
   */
  const resetPdf = () => {
    setNumPages(0);
    setScale(1);
    setPdfTitle(null);
    setBase64Pdf(null);
    setInitialPageIndex(0);
  };

  /**
   * PDFの表示を拡大する
   */
  const zoomIn = () => {
    setScale(Math.min((scale * 10 + 1) / 10, 10));
  };

  /**
   * PDFの表示を縮小する
   */
  const zoomOut = () => {
    setScale(Math.max((scale * 10 - 1) / 10, 0.4));
  };

  return {
    pdfTitle,
    setPdfTitle,
    base64Pdf,
    resetPdf,
    fetchBase64Pdf,
    numPages,
    setNumPages,
    scale,
    zoomIn,
    zoomOut,
    initialPageIndex,
    fetchBase64PdfWithSpecificPage,
    resetInitialPageIndex,
  };
};
