"use client";
import { updateCollection } from "@/actions/collection";
import { MinusIcon } from "@/components/icons/minusIcon";
import { OpenPdfIcon } from "@/components/icons/openPdfIcon";
import {
  CardCategory,
  DocumentIcon,
  isPdf,
  isPlainText,
} from "@/components/utils/document";
import { useCollection } from "@/hooks/collection/useCollection";
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
 * パネルドキュメントカードのカスタムフック
 * @param document - ドキュメント情報
 * @returns カードの各要素と操作関数を含むオブジェクト
 */
export const usePanelDocumentCard = (document: DocumentType) => {
  const { commonButtonDisabled, buttonColor, setCommonButtonDisabled } =
    useButtonDisabled();
  const { fetchBase64Pdf, resetPdf } = usePdf();
  const { fetchText, resetText } = usePlainText();
  const { collection, setCollection, getDocumentIds } = useCollection();
  const { showError, errorTemplate } = useError();

  /**
   * ドキュメントを削除する関数
   */
  const removeDocument = async () => {
    if (!collection) {
      return;
    }
    setCommonButtonDisabled(true);
    try {
      const currentDocumentIds = getDocumentIds();
      const updateDocumentIds = currentDocumentIds.filter((id) => id !== document.id);
      const resultCollection = await updateCollection(collection.public_collection_id, {
        name: collection.name,
        document_ids: updateDocumentIds,
      });
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
      <form action={removeDocument}>
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
  return {
    OpenDocumentIcon,
    RemoveDocumentIcon,
    CardCategoryArea,
  };
};

/**
 * パネルドキュメントカードコンポーネント
 * @param props - カードのプロパティ
 * @returns ドキュメントカードのJSX要素
 */
const PanelDocumentCard = (props: Props) => {
  const { className, document } = props;
  const { OpenDocumentIcon, RemoveDocumentIcon, CardCategoryArea } =
    usePanelDocumentCard(document);

  return (
    <BaseDocumentCard
      className={className}
      document={document}
      CardCategoryArea={<CardCategoryArea />}
      DocumentIcon={<DocumentIcon document={document} />}
      OpenDocumentIcon={<OpenDocumentIcon />}
      // AddDocumentIcon ドキュメント追加はしないので不要
      CloseIcon={<RemoveDocumentIcon />}
    />
  );
};

export default PanelDocumentCard;
