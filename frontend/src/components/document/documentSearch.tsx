"use client";

import SearchDocumentCard from "@/components/document/card/searchDocumentCard";
import { DocumentSearchFilter } from "@/components/document/documentSearchFilter";
import FilterIcon from "@/components/icons/filterIcon";
import { DRAG_ITEM_TYPES } from "@/consts/draggable";
import { useSearchedDocumentDrop } from "@/hooks/collection/document/useDragDropSearchCollectionDocuments";
import { useSearchCollectionDocuments } from "@/hooks/collection/document/useSearchCollectionDocuments";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { AUTOSAR, DocumentType } from "@/models/document";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";
import { useState } from "react";
import { MinusIcon } from "../icons/minusIcon";
import { DeleteConfirmModal } from "@/components/modal/collection/deleteConfirmModal";
import { useModal } from "@/hooks/useModal";
import { Fragment } from "react";

/**
 * ドキュメント検索機能のカスタムフック
 * @returns ドキュメント検索に関する状態と操作関数を含むオブジェクト
 */
export const useDocumentSearch = () => {
  const { commonButtonDisabled, buttonColor } = useButtonDisabled();
  const {
    message,
    pageCount,
    currentPage,
    inputValue,
    setInputValue,
    searchedDocuments,
    searchDocuments,
    handleChangePage,
    deleteUploadedDocument,
  } = useSearchCollectionDocuments();
  const [isVisibleFilter, setIsVisibleFilter] = useState<boolean>(false);
  const { dropRef } = useSearchedDocumentDrop();
  const { isOpen, showModal, hideModal } = useModal();
  const [targetDocumentId, setTargetDocumentId] = useState<string | null>(null);

  /**
   * ドキュメント検索のサブミットハンドラー
   * @param event - フォームのサブミットイベント
   */
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); // ページ遷移を防ぐ
    await searchDocuments();
  };

  /**
   * ドキュメント削除ハンドラー
   * @param confirmed - 削除確認ダイアログの結果
   * @param document - 削除対象のドキュメント
   */
  const handleDelete = async (confirmed: boolean, document: DocumentType) => {
    if (confirmed) {
      await deleteUploadedDocument(document);
    }
    setTargetDocumentId(null);
    hideModal();
  };

  /**
   * ドキュメント削除コンポーネント
   * @param props - ドキュメント情報を含むプロパティ
   * @returns ドキュメント削除ボタンのJSX要素またはnull
   */
  const RemoveDocument = ({ document }: { document: DocumentType }) => {
    const removable = document.subject !== AUTOSAR;
    return removable ? (
      <button
        className="ml-1"
        onClick={(e) => {
          setTargetDocumentId(document.id);
          showModal(e);
        }}
        disabled={commonButtonDisabled}
        data-testid="deleteDocumentButton"
      >
        <MinusIcon className="w-6 h-6" color={buttonColor} />
      </button>
    ) : null;
  };

  return {
    inputValue,
    setInputValue,
    searchedDocuments,
    message,
    pageCount,
    currentPage,
    isVisibleFilter,
    setIsVisibleFilter,
    isOpen,
    handleSubmit,
    handleChangePage,
    dropRef,
    RemoveDocument,
    handleDelete,
    targetDocumentId,
  };
};

/**
 * ドキュメント検索のビューコンポーネント
 * @param hooks - カスタムフックの戻り値
 * @returns ドキュメント検索画面のJSX要素
 */
export const DocumentSearchView = ({
  hooks,
}: {
  hooks: ReturnType<typeof useDocumentSearch>;
}) => {
  return (
    <div
      ref={hooks.dropRef}
      className="w-full h-full flex-col flex items-center justify-start gap-3 overflow-auto"
    >
      <div className="inline-flex items-center justify-end w-10/12 py-2">
        <div className="border-2 border-solid border-white shadow-[0px_2px_12px_#aaaaaa1f] rounded-2xl bg-[#ffffff99] flex-grow">
          <div className="[font-family:'Noto_Sans_JP-Regular',Helvetica]">
            <form onSubmit={hooks.handleSubmit}>
              <input
                type="text"
                name="inputValue"
                placeholder="キーワード"
                className="w-full p-2 outline-none bg-transparent"
                value={hooks.inputValue}
                onChange={(e) => hooks.setInputValue(e.target.value)}
              />
            </form>
          </div>
        </div>
        <div className="px-3">
          <button type="button" onClick={() => hooks.setIsVisibleFilter(true)}>
            <FilterIcon />
          </button>
        </div>
      </div>
      <DocumentSearchFilter
        isVisible={hooks.isVisibleFilter}
        onClose={() => hooks.setIsVisibleFilter(false)}
      />
      <div className="flex flex-col items-center grow w-full gap-3">
        {hooks.message ? (
          <div className="grow w-full pl-28 py-4 [font-family:'Hiragino_Sans-W4',Helvetica] text-pale-blue">
            <p>{hooks.message}</p>
          </div>
        ) : (
          <>
            {hooks.searchedDocuments.map((document, index) => (
              <Fragment key={index}>
                <SearchDocumentCard
                  className={"w-10/12"}
                  document={document}
                  RemoveDocument={<hooks.RemoveDocument document={document} />}
                  dragItemType={DRAG_ITEM_TYPES.SEARCHED_DOCUMENT}
                />
                <DeleteConfirmModal
                  isModalOpen={hooks.isOpen && hooks.targetDocumentId === document.id}
                  onClose={(confirmed) => hooks.handleDelete(confirmed, document)}
                  title="アップロードしたファイルを削除"
                  message={`${document.title}\n\n上記ファイルを削除しますか？`}
                />
              </Fragment>
            ))}
          </>
        )}
      </div>
      {hooks.pageCount > 0 && (
        <div className="w-full flex justify-center pb-2">
          <Stack spacing={2}>
            <Pagination
              count={hooks.pageCount}
              page={hooks.currentPage}
              variant="outlined"
              siblingCount={2}
              color="primary"
              onChange={(e, index) => hooks.handleChangePage(index)}
            />
          </Stack>
        </div>
      )}
    </div>
  );
};

/**
 * ドキュメント検索のメインコンポーネント
 * @returns ドキュメント検索画面のJSX要素
 */
const DocumentSearch = () => {
  const hooks = useDocumentSearch();
  return <DocumentSearchView hooks={hooks} />;
};

export default DocumentSearch;
