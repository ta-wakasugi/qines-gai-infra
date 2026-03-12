"use client";
import { getCollectionDetail } from "@/actions/collection";
import CollectionEdit from "@/components/collection/collectionEdit";
import DocumentSearch from "@/components/document/documentSearch";
import { ErrorAlert } from "@/components/error/errorAlert";
import BaseHeader from "@/components/header/baseHeader";
import PageLoading from "@/components/loading/pageLoading";
import Background from "@/components/utils/Background";
import BackgroundUploadFilter from "@/components/utils/BackgroundUploadFilter";
import { useSearchCollectionDocuments } from "@/hooks/collection/document/useSearchCollectionDocuments";
import { useCollection } from "@/hooks/collection/useCollection";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { useDragDropUpload } from "@/hooks/useDragDropUpload";
import { useError } from "@/hooks/useError";
import { useLoading } from "@/hooks/useLoading";
import { useEffect } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { ViewerContainer } from "@/components/conversation/viewerContainer";

type Props = {
  collection_id: string;
};

/**
 * 既存コレクション編集ページのコンポーネント
 * コレクションの詳細表示、編集、文書管理機能を提供する
 * @param params - URLパラメータ（collection_id）を含むオブジェクト
 * @returns JSX.Element
 */
export default function Collection({ params }: { params: Props }) {
  const { collection, setCollection } = useCollection();
  const { setCollectionDocuments } = useSearchCollectionDocuments();
  const { loadingText } = useLoading();
  const { getRootProps, getInputProps, isDragActive, open } = useDragDropUpload();
  const { base64Pdf } = usePdf();
  const { textContent } = usePlainText();
  const { showError, errorTemplate } = useError();
  useEffect(() => {
    (async () => {
      try {
        const res = await getCollectionDetail(params.collection_id);
        setCollectionDocuments(res.documents);
        setCollection(res);
      } catch (e) {
        console.error(e);
        showError(errorTemplate.api);
      }
    })();
  }, []);
  return (
    <>
      {/* TODO: 新規コレクション画面との共通化*/}
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
                collectionName={collection?.name ?? ""}
                uploadInputProps={getInputProps}
                uploadDialogOpen={open}
              />
            </div>
            {/* 右側部分 */}
            <div className="w-1/2 flex-col flex items-center justify-start gap-3 overflow-auto">
              {(textContent || base64Pdf) && (
                <div className="fixed z-10" style={{ width: "49vw" }}>
                  <ViewerContainer />
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
