import {
  CardCategory,
  DocumentIcon,
  isPdf,
  isPlainText,
} from "@/components/utils/document";
import {
  useCollectionDocumentDrag,
  useSearchedDocumentDrag,
} from "@/hooks/collection/document/useDragDropSearchCollectionDocuments";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { DocumentType } from "@/models/document";
import { ReactElement } from "react";
import { DRAG_ITEM_TYPES, ItemOfDragItemType } from "../../../consts/draggable";
import BaseDocumentCard from "./baseDocumentCard";

interface Props {
  className: string;
  document: DocumentType;
  dragItemType: ItemOfDragItemType;
  RemoveDocument: ReactElement;
}

/**
 * 検索結果ドキュメントカードのカスタムフック
 * @param document - ドキュメント情報
 * @param dragItemType - ドラッグ＆ドロップのアイテムタイプ
 * @returns カードの各要素とドラッグ参照を含むオブジェクト
 */
export const useSearchDocumentCard = (
  document: DocumentType,
  dragItemType: ItemOfDragItemType
) => {
  const { commonButtonDisabled } = useButtonDisabled();
  const { fetchBase64Pdf, resetPdf } = usePdf();
  const { fetchText, resetText } = usePlainText();
  const { dragRef: searchedDrag } = useSearchedDocumentDrag(document);
  const { dragRef: collectionDrag } = useCollectionDocumentDrag(document);
  const dragRef =
    dragItemType === DRAG_ITEM_TYPES.SEARCHED_DOCUMENT ? searchedDrag : collectionDrag;

  /**
   * ドキュメントを開くボタンコンポーネント
   * @returns ドキュメントを開くボタンのJSX要素またはnull
   */
  const OpenDocumentIcon = () => {
    if (!isPdf(document) && !isPlainText(document)) {
      return null;
    }

    const handleOpenDocument = isPdf(document)
      ? async () => {
          // PDFを開く前にテキストをリセット
          resetText();
          await fetchBase64Pdf(document);
        }
      : async () => {
          // テキストを開く前にPDFをリセット
          resetPdf();
          await fetchText(document);
        };

    return (
      <form action={handleOpenDocument}>
        <button
          className="border border-solid border-light-gray rounded-lg px-4 py-2"
          disabled={commonButtonDisabled}
          data-testid="openDocumentButton"
        >
          <div
            className={`[font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal text-sm ${commonButtonDisabled ? "text-pale-blue" : "text-action-blue"}`}
          >
            開く
          </div>
        </button>
      </form>
    );
  };

  /**
   * ドキュメントカテゴリー表示エリアコンポーネント
   * @returns カテゴリー表示エリアのJSX要素
   */
  const CardCategoryArea = () => {
    return (
      <div
        className={`items-center flex-[0_0_auto] flex self-stretch justify-between`}
        data-testid="cardCategoryArea"
      >
        <CardCategory document={document} />
      </div>
    );
  };
  return {
    OpenDocumentIcon,
    CardCategoryArea,
    dragRef,
  };
};

/**
 * 検索結果ドキュメントカードコンポーネント
 * @param props - カードのプロパティ
 * @returns ドキュメントカードのJSX要素
 */
const SearchDocumentCard = (props: Props) => {
  const { className, document } = props;
  const { OpenDocumentIcon, CardCategoryArea, dragRef } = useSearchDocumentCard(
    document,
    props.dragItemType
  );

  return (
    <BaseDocumentCard
      className={className}
      document={document}
      CardCategoryArea={<CardCategoryArea />}
      DocumentIcon={<DocumentIcon document={document} />}
      OpenDocumentIcon={<OpenDocumentIcon />}
      // AddDocumentIcon ドキュメント追加はDrag&Dropなので不要
      CloseIcon={props.RemoveDocument}
      dragRef={dragRef}
      isVerticalButtons={true}
    />
  );
};

export default SearchDocumentCard;
