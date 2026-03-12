import { FileIcon } from "@/components/icons/fileIcon";
import { PdfIcon } from "@/components/icons/pdfIcon";
import { AUTOSAR, DocumentType } from "@/models/document";

/**
 * ドキュメントがPDFかどうかを判定する関数
 * @param document - ドキュメント情報
 * @returns PDFの場合はtrue
 */
export const isPdf = (document: DocumentType) => {
  return document.file_type === "application/pdf";
};

/**
 * ドキュメントがプレインテキストかどうかを判定する関数
 * @param document - ドキュメント情報
 * @returns プレインテキストの場合はtrue
 */
export const isPlainText = (document: DocumentType) => {
  return (
    document.file_type?.startsWith("text/") ||
    document.title?.endsWith(".md") ||
    document.title?.endsWith(".txt")
  );
};

/**
 * ドキュメントがマークダウンかどうかを判定する関数
 * @param document - ドキュメント情報
 * @returns マークダウンの場合はtrue
 */
export const isMarkdown = (document: DocumentType) => {
  return (
    document.file_type === "text/markdown" ||
    (document.file_type === "text/plain" && document.title?.endsWith(".md"))
  );
};

interface DocumentIconProps {
  document: DocumentType;
}

/**
 * ドキュメントアイコンコンポーネント
 * @param props - コンポーネントのプロパティ
 * @returns PDFまたは一般ファイルのアイコンJSX要素
 */
export const DocumentIcon = ({ document }: DocumentIconProps) => {
  return isPdf(document) ? (
    <PdfIcon className="w-5 h-5" />
  ) : (
    <FileIcon className="w-5 h-5" />
  );
};

interface CardCategoryProps {
  document: DocumentType;
}

/**
 * カードカテゴリーコンポーネント
 * @param props - コンポーネントのプロパティ
 * @returns カテゴリー情報のJSX要素またはnull
 */
export const CardCategory = ({ document }: CardCategoryProps) => {
  if (document.subject !== AUTOSAR) return null;
  return (
    <div className="flex self-stretch items-center grow flex-1 text-gray-400">
      <div className="text-sm text-pale-blue font-normal leading-7 whitespace-nowrap">
        {document.genre}
      </div>
      <div className="text-sm text-pale-blue font-normal leading-7 whitespace-nowrap">
        ・
      </div>
      <div className="text-sm text-pale-blue font-normal leading-7 whitespace-nowrap">
        {document.release}
      </div>
    </div>
  );
};
