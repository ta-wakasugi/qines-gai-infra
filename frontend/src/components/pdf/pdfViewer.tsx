"use client";
import IntegerInput from "@/components/input/integerInput";
import { THEME_COLORS } from "@/consts/color";
import { usePdf } from "@/hooks/pdf/usePdf";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Document, DocumentProps, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Virtuoso, VirtuosoHandle } from "react-virtuoso";
import { CloseIcon } from "../icons/closeIcon";
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.js",
  import.meta.url
).toString();

type Props = {
  width?: string;
  height?: string;
};

const mockedBtnClass =
  "w-8 h-8 text-2xl text-gray-500 hover:bg-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-gray-400";

type PdfSize = {
  width: number;
  height: number;
};

type OnItemClick = Required<DocumentProps>["onItemClick"];

/**
 * PDFビューワーのカスタムフック
 * @returns PDFビューワーの状態と操作関数を含むオブジェクト
 */
export const usePdfViewer = () => {
  const {
    numPages,
    setNumPages,
    scale,
    zoomIn,
    zoomOut,
    initialPageIndex,
    base64Pdf,
    pdfTitle,
    resetPdf,
  } = usePdf();
  const ref = useRef<VirtuosoHandle | null>(null);
  const [pdfSize, setPdfSize] = useState<PdfSize>({ width: 0, height: 0 });
  const [visiblePage, setVisiblePage] = useState(0);
  const setVisibleRange = useCallback(
    (range: { startIndex: number; endIndex: number }) => {
      setVisiblePage(range.endIndex);
    },
    []
  );

  const dataUrl = `data:application/pdf;base64,${base64Pdf}`;

  // initialPageIndexが変更されたら該当ページへスクロール
  useEffect(() => {
    if (ref.current && initialPageIndex > 0) {
      ref.current.scrollToIndex({ index: initialPageIndex });
    }
  }, [initialPageIndex]);

  useEffect(() => {
    if (!base64Pdf || base64Pdf.length === 0) return;

    // PDFファイルのマジックナンバーをチェック
    try {
      const binaryString = atob(base64Pdf);
      if (!binaryString.startsWith("%PDF")) {
        return;
      }
    } catch (e) {
      return;
    }

    (async () => {
      try {
        const pdf = await pdfjs.getDocument(dataUrl).promise;
        const numPages = pdf.numPages;
        setNumPages(numPages);
        const viewport = (await pdf.getPage(1)).getViewport({ scale });
        setPdfSize({
          width: scale * viewport.width,
          height: scale * viewport.height,
        });
      } catch (error) {
        console.error("PDF解析エラー:", error);
      }
    })();
  }, [dataUrl, base64Pdf]);

  /**
   * 指定ページへジャンプする関数
   * @param e - フォームイベント
   */
  const jumpToPage = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const value = form.get("value");
    if (ref.current)
      ref.current.scrollToIndex({
        index: Number(value) - 1,
      });
  };

  /**
   * 内部リンクでジャンプする関数
   * @param args - リンクに関する情報
   */
  const jumpByLink: OnItemClick = ({ pageIndex }) =>
    ref.current?.scrollToIndex({ index: pageIndex });

  /**
   * PDFページを表示するコンポーネント
   * @param props - コンポーネントのプロパティ
   * @returns PDFページのJSX要素
   */
  const Row = ({ index, pdfSize }: { index: number; pdfSize: PdfSize }) => (
    <div className="flex justify-center items-center bg-[#A5ACAE] pt-3">
      {/* Note: loadingのサイズをPDFに合わせることでスクロール時や初期レンダリング時のチラつきを防止可能 */}
      <Page
        scale={scale}
        pageIndex={index}
        className="relative"
        loading={
          <div
            style={{
              width: pdfSize.width,
              height: pdfSize.height,
            }}
          >
            Loading...
          </div>
        }
      />
    </div>
  );

  return {
    ref,
    dataUrl,
    numPages,
    scale,
    zoomIn,
    zoomOut,
    jumpToPage,
    jumpByLink,
    Row,
    pdfTitle,
    resetPdf,
    pdfSize,
    initialPageIndex,
    visiblePage,
    setVisibleRange,
    base64Pdf,
  };
};

type HooksType = ReturnType<typeof usePdfViewer>;

/**
 * PDFビューワーのレイアウトコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns PDFビューワーのJSX要素
 */
export const PdfViewerLayout = ({
  hooks,
  props,
}: {
  hooks: HooksType;
  props: Props;
}) => {
  const {
    ref,
    dataUrl,
    numPages,
    scale,
    zoomIn,
    zoomOut,
    jumpToPage,
    jumpByLink,
    Row,
    resetPdf,
    pdfSize,
    initialPageIndex,
    visiblePage,
    setVisibleRange,
    base64Pdf,
  } = hooks;
  const height = props.height ? props.height : "95vh";
  const width = props.width ? props.width : "45vw";
  const memoizedDocument = useMemo(() => {
    if (!base64Pdf || base64Pdf.length === 0) return null;

    return (
      <Document file={dataUrl} onItemClick={jumpByLink}>
        <Virtuoso
          style={{ height, width }}
          totalCount={numPages}
          ref={ref}
          initialTopMostItemIndex={initialPageIndex}
          itemContent={(index) => {
            return <Row index={index} pdfSize={pdfSize} />;
          }}
          rangeChanged={setVisibleRange}
        />
      </Document>
    );
  }, [
    dataUrl,
    numPages,
    ref,
    initialPageIndex,
    pdfSize,
    height,
    width,
    scale,
    base64Pdf,
  ]);

  // 親コンテナに対する固定比率でバー位置を設定
  const bottomPosition = "bottom-[5%]";

  return (
    <>
      <div className="relative border rounded-xl rounded-b-none bg-white">
        <div className="flex border justify-between items-center bg-white py-1 px-2 rounded-xl rounded-b-none">
          <div className="ml-2">{hooks.pdfTitle}</div>
          <button className="text-action-blue text-2xl mr-2" onClick={hooks.resetPdf}>
            ×
          </button>
        </div>
        {memoizedDocument}
        {/* pdfメニュー */}
        <div
          className={`flex w-[300px] items-center gap-10 pl-3 pr-2 py-1 z-10 absolute ${bottomPosition} left-0 right-0 mx-auto bg-gray-200 rounded-[32px] opacity-85`}
        >
          <div className="inline-flex items-center gap-9 relative flex-[0_0_auto]">
            <div className="inline-flex items-center gap-2 relative flex-[0_0_auto]">
              <button
                onClick={zoomOut}
                className={mockedBtnClass}
                data-testid="zoomOutButton"
              >
                −
              </button>
              <button
                onClick={zoomIn}
                className={mockedBtnClass}
                data-testid="zoomInButton"
              >
                +
              </button>
            </div>
            <div className="inline-flex items-center gap-4 relative flex-[0_0_auto]">
              <form onSubmit={jumpToPage}>
                <IntegerInput
                  min={1}
                  max={hooks.numPages}
                  defaultValue={String(visiblePage + 1)}
                  className="w-12 text-center"
                />{" "}
                / {hooks.numPages}
              </form>
            </div>
            <button onClick={resetPdf}>
              <CloseIcon className="w-6 h-6" color={THEME_COLORS.button} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

/**
 * PDFビューワーのメインコンポーネント
 * @param props - コンポーネントのプロパティ
 * @returns PDFビューワーのJSX要素
 */
const PdfViewer = (props: Props) => {
  const hooks = usePdfViewer();

  // PDFデータが存在しない場合、または有効なPDFでない場合は何も表示しない
  if (!hooks.base64Pdf) {
    return null;
  }

  // PDFマジックナンバーをチェック
  try {
    const binaryString = atob(hooks.base64Pdf);
    if (!binaryString.startsWith("%PDF")) {
      return null;
    }
  } catch (e) {
    return null;
  }

  return <PdfViewerLayout hooks={hooks} props={props} />;
};

export default PdfViewer;
