"use client";
import CollectionEdit from "@/components/collection/collectionEdit";
import DocumentSearch from "@/components/document/documentSearch";
import { ErrorAlert } from "@/components/error/errorAlert";
import BaseHeader from "@/components/header/baseHeader";
import PageLoading from "@/components/loading/pageLoading";
import Background from "@/components/utils/Background";
import BackgroundUploadFilter from "@/components/utils/BackgroundUploadFilter";
import { useSearchCollectionDocuments } from "@/hooks/collection/document/useSearchCollectionDocuments";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { useDragDropUpload } from "@/hooks/useDragDropUpload";
import { useLoading } from "@/hooks/useLoading";
import dynamic from "next/dynamic";
import { useEffect } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
const PdfViewer = dynamic(() => import("@/components/pdf/pdfViewer"), {
  ssr: false,
});

/**
 * 新規コレクション作成ページのコンポーネント
 * PDF文書のアップロードとコレクション情報の編集機能を提供する
 * @returns JSX.Element
 */
export default function NewCollection() {
  const { setCollectionDocuments } = useSearchCollectionDocuments();
  const { loadingText } = useLoading();
  const { getRootProps, getInputProps, isDragActive, open } = useDragDropUpload();
  const { base64Pdf } = usePdf();
  const { textContent, textTitle, resetText } = usePlainText();
  useEffect(() => {
    setCollectionDocuments([]);
  }, []);
  return (
    <>
      <ErrorAlert />
      <div className="h-screen" {...getRootProps()}>
        <Background className="left-1/2" />
        <BackgroundUploadFilter
          isDisplay={isDragActive}
          className="w-full"
          text={`ドラッグして\nコレクションにファイルを追加`}
        />
        <BaseHeader />
        <PageLoading text={loadingText} />
        <DndProvider backend={HTML5Backend}>
          <div className="relative flex h-[91vh]">
            {/* 左側部分 */}
            <div className="w-1/2 flex flex-col">
              <CollectionEdit
                collectionName=""
                uploadInputProps={getInputProps}
                uploadDialogOpen={open}
              />
            </div>
            {/* 右側部分 */}
            <div className="w-1/2 flex-col flex items-center justify-start gap-3 overflow-auto">
              {textContent && !base64Pdf && (
                <div className="fixed z-10">
                  <div
                    className="relative border rounded-xl bg-white"
                    style={{ width: "49vw", height: "87vh" }}
                  >
                    <div className="flex border justify-between items-center bg-white py-1 px-2 rounded-xl rounded-b-none">
                      <div className="ml-2">{textTitle}</div>
                      <button
                        className="text-action-blue text-2xl mr-2"
                        onClick={resetText}
                      >
                        ×
                      </button>
                    </div>
                    <div
                      className="p-4 overflow-auto bg-white"
                      style={{ height: "calc(87vh - 40px)" }}
                    >
                      <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                        {textContent}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
              {base64Pdf && !textContent && (
                <div className="fixed z-10">
                  <PdfViewer width="49vw" height="87vh" />
                </div>
              )}
              <DocumentSearch />
            </div>
          </div>
        </DndProvider>
      </div>
    </>
  );
}
