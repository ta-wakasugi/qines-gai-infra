"use client";

import { SaveButton } from "@/components/button/saveButton";
import { BackIcon } from "@/components/icons/backIcon";
import { FolderIcon } from "@/components/icons/folderIcon";
import { SaveCollectionModal } from "@/components/modal/collection/saveCollectionModal";
import { DRAG_ITEM_TYPES } from "@/consts/draggable";
import { DISPLAY_PATH } from "@/consts/paths";
import { useCollectionDocumentDrop } from "@/hooks/collection/document/useDragDropSearchCollectionDocuments";
import { useSearchCollectionDocuments } from "@/hooks/collection/document/useSearchCollectionDocuments";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useModal } from "@/hooks/useModal";
import { DocumentType } from "@/models/document";
import { DropzoneInputProps } from "react-dropzone";
import SearchDocumentCard from "../document/card/searchDocumentCard";
import { MinusIcon } from "../icons/minusIcon";
import FileUploader from "../input/fileUploader";
import { THEME_COLORS } from "@/consts/color";

type Props = {
  collectionName: string;
  uploadInputProps: <T extends DropzoneInputProps>(props?: T) => T;
  uploadDialogOpen: () => void;
};

/** コレクション編集画面のカスタムフック */
const useCollectionEdit = (collectionName: string) => {
  // TODO: ドキュメントリストの編集機能が実装されたらeditingDocumentsを利用する
  const { collectionDocuments, collectionDocumentsIds, removeFromCollection } =
    useSearchCollectionDocuments();
  const { isOpen, showModal, hideModal } = useModal();
  const { commonButtonDisabled, buttonColor } = useButtonDisabled();
  const { dropRef } = useCollectionDocumentDrop();
  const displayCollectionName =
    collectionName === "" ? "新規コレクション" : collectionName;
  const RemoveDocument = (document: DocumentType) => {
    const handleRemoveDocument = () => {
      removeFromCollection(document);
    };
    return (
      <form action={handleRemoveDocument}>
        <button
          className="ml-1"
          disabled={commonButtonDisabled}
          data-testid="deleteDocumentButton"
        >
          <MinusIcon className="w-6 h-6" color={buttonColor} />
        </button>
      </form>
    );
  };

  return {
    displayCollectionName,
    isOpen,
    showModal,
    hideModal,
    commonButtonDisabled,
    collectionDocuments,
    collectionDocumentsIds,
    dropRef,
    RemoveDocument,
  };
};

type hooks = ReturnType<typeof useCollectionEdit>;

/** コレクション編集画面のビューコンポーネント */
const CollectionEditView = ({ props, hooks }: { props: Props; hooks: hooks }) => {
  const uploadButtonLabel = `ローカルのファイルを\nここにドラッグしてアップロード`;
  return (
    <div ref={hooks.dropRef} className="w-full h-full flex flex-col">
      <div className="inline-flex items-center w-full">
        <a
          href={DISPLAY_PATH.COLLECTION.LIST}
          className="relative mt-1 inline-flex items-center text-action-blue hover:underline hover:cursor-pointer"
        >
          <BackIcon color={THEME_COLORS.button} className="w-8 h-8 ml-1" />
          <div className="[font-family:'Hiragino_Sans-W3',Helvetica] text-action-blue hover:underline ">
            コレクション一覧
          </div>
        </a>
      </div>
      <div className="inline-flex items-center w-full gap-3 px-2">
        <FolderIcon className={"w-9 h-9"} />
        <div className="[font-family:'Hiragino_Sans-W5',Helvetica] text-2xl relative">
          {hooks.displayCollectionName}
        </div>
      </div>
      {hooks.collectionDocuments.length > 0 ? (
        <div className="grow w-full px-14 py-4 flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 w-full overflow-y-auto">
            {hooks.collectionDocuments.map((document) => (
              <SearchDocumentCard
                key={document.id}
                className="pb-4 w-full pr-1"
                document={document}
                RemoveDocument={hooks.RemoveDocument(document)}
                dragItemType={DRAG_ITEM_TYPES.COLLECTION_DOCUMENT}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="grow w-full px-14 py-4 [font-family:'Hiragino_Sans-W4',Helvetica] font-normal text-pale-blue">
          ファイルをドラッグ&amp;ドロップしてください。
        </div>
      )}
      <div className="mx-auto w-11/12 mb-1">
        <FileUploader
          getInputProps={props.uploadInputProps}
          buttonLabel={uploadButtonLabel}
          isUploadOnly={true}
          open={props.uploadDialogOpen}
        />
      </div>
      <div className="flex justify-center items-center">
        <SaveButton
          className="w-5/6"
          onClick={hooks.showModal}
          disabled={hooks.commonButtonDisabled}
        >
          保存
        </SaveButton>
      </div>
      <SaveCollectionModal
        isModalOpen={hooks.isOpen}
        handleCloseModal={hooks.hideModal}
        documentIds={hooks.collectionDocumentsIds}
      />
    </div>
  );
};

/**
 * コレクション編集画面のメインコンポーネント。
 * ドキュメントの追加・削除、コレクションの保存機能を提供する
 *
 * @param {Props} props - コレクション名とアップロード関連のプロパティ
 * @returns {JSX.Element} コレクション編集画面のコンポーネント
 */
/**
 * `CollectionEdit`コンポーネントは、コレクションの編集を担当します。
 * `useCollectionEdit`フックを利用して、コレクションの編集に必要な状態とロジックを管理します。
 * このコンポーネントは、必要なプロパティとフックを渡して`CollectionEditView`コンポーネントをレンダリングします。
 *
 * @param props - コンポーネントに渡されるプロパティ。
 * @param props.collectionName - 編集するコレクションの名前。
 * @returns コレクション編集ビューを表すJSX要素。
 */
const CollectionEdit = (props: Props) => {
  const hooks = useCollectionEdit(props.collectionName);
  return <CollectionEditView props={props} hooks={hooks} />;
};

export default CollectionEdit;
