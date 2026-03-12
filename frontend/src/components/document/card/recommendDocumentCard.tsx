"use client";
import { updateCollection } from "@/actions/collection";
import { CloseIcon } from "@/components/icons/closeIcon";
import { OpenPdfIcon } from "@/components/icons/openPdfIcon";
import {
  CardCategory,
  DocumentIcon,
  isPdf,
  isPlainText,
} from "@/components/utils/document";
import { useCollection } from "@/hooks/collection/useCollection";
import { useRecommendDocuments } from "@/hooks/conversation/useRecommendDocuments";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import { DocumentType } from "@/models/document";
import BaseDocumentCard from "./baseDocumentCard";

interface Props {
  className: string;
  document: DocumentType;
}

/**
 * おすすめドキュメントカードのカスタムフック
 * @param document - ドキュメント情報
 * @returns カードの各要素と操作関数を含むオブジェクト
 */
export const useRecommendDocumentCard = (document: DocumentType) => {
  const { commonButtonDisabled, setCommonButtonDisabled, buttonColor } =
    useButtonDisabled();
  const { fetchBase64Pdf, resetPdf } = usePdf();
  const { fetchText, resetText } = usePlainText();
  const { deleteRecommendDocument } = useRecommendDocuments();
  const { collection, setCollection, getDocumentIds } = useCollection();
  const { showError, errorTemplate } = useError();

  /**
   * コレクションにドキュメントを追加する関数
   */
  const addCollectionDocument = async () => {
    if (!collection) {
      return;
    }
    setCommonButtonDisabled(true);
    try {
      const currentDocumentIds = getDocumentIds();
      currentDocumentIds.push(document.id);
      const resultCollection = await updateCollection(collection.public_collection_id, {
        name: collection.name,
        document_ids: currentDocumentIds,
      });
      deleteRecommendDocument(document.id);
      setCollection(resultCollection);
    } catch (error) {
      showError(errorTemplate.api);
      console.error(error);
    } finally {
      setCommonButtonDisabled(false);
    }
  };

  /**
   * ドキュメントを開くボタンコンポーネント
   * @returns ドキュメントを開くボタンのJSX要素またはnull
   */
  const OpenDocumentIcon = () => {
    if (isPdf(document)) {
      const handlePdfOpen = async () => {
        resetText();
        await fetchBase64Pdf(document);
      };
      return (
        <form action={handlePdfOpen}>
          <button
            className="ml-1"
            disabled={commonButtonDisabled}
            data-testid="openPdfButton"
          >
            <OpenPdfIcon className="w-6 h-6" color={buttonColor} />
          </button>
        </form>
      );
    }
    if (isPlainText(document)) {
      const handlePlainTextOpen = async () => {
        resetPdf();
        await fetchText(document);
      };
      return (
        <form action={handlePlainTextOpen}>
          <button
            className="ml-1"
            disabled={commonButtonDisabled}
            data-testid="openPdfButton"
          >
            <OpenPdfIcon className="w-6 h-6" color={buttonColor} />
          </button>
        </form>
      );
    }
    return null;
  };

  /**
   * ドキュメントを削除するボタンコンポーネント
   * @returns 削除ボタンのJSX要素
   */
  const RemoveDocumentIcon = () => {
    return (
      <form>
        <button
          className="ml-1"
          onClick={() => deleteRecommendDocument(document.id)}
          data-testid="deleteRecommendButton"
        >
          <CloseIcon className="w-6 h-6" color={buttonColor} />
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
        className={`items-center flex-[0_0_auto] w-full flex self-stretch justify-between`}
        data-testid="cardCategoryArea"
      >
        <CardCategory document={document} />
      </div>
    );
  };

  /**
   * ドキュメント追加ボタンコンポーネント
   * @returns 追加ボタンのJSX要素
   */
  const AddDocumentButton = () => {
    return (
      <form
        action={addCollectionDocument}
        className="flex justify-center items-center w-full mt-3 mb-1"
        data-testid="addDocumentForm"
      >
        <button
          className="w-full bg-action-blue text-white rounded-lg py-2"
          disabled={commonButtonDisabled}
          data-testid="addDocumentButton"
        >
          追加する
        </button>
      </form>
    );
  };
  return {
    OpenDocumentIcon,
    RemoveDocumentIcon,
    CardCategoryArea,
    AddDocumentButton,
  };
};

/**
 * おすすめドキュメントカードコンポーネント
 * @param props - カードのプロパティ
 * @returns ドキュメントカードのJSX要素
 */
const RecommendDocumentCard = ({ className, document }: Props) => {
  const { OpenDocumentIcon, RemoveDocumentIcon, CardCategoryArea, AddDocumentButton } =
    useRecommendDocumentCard(document);

  return (
    <BaseDocumentCard
      className={className}
      document={document}
      CardCategoryArea={<CardCategoryArea />}
      DocumentIcon={<DocumentIcon document={document} />}
      OpenDocumentIcon={<OpenDocumentIcon />}
      AddDocumentIcon={<AddDocumentButton />}
      CloseIcon={<RemoveDocumentIcon />}
    />
  );
};

export default RecommendDocumentCard;
