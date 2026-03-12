"use client";
import { usePdf } from "@/hooks/pdf/usePdf";
import { usePlainText } from "@/hooks/text/usePlainText";
import { ContextType } from "@/models/conversation";
import Accordion from "../utils/accordion";

type Props = {
  references: ContextType[];
};

/**
 * ファイルタイプがPDFかどうかを判定
 */
const isPdfFileType = (fileType: string | undefined): boolean => {
  return fileType === "application/pdf";
};

/**
 * メッセージの参照情報をアコーディオン形式で表示するコンポーネント
 * @param {Props} props - 参照情報の配列
 */
export const MessageReference = (props: Props) => {
  const { fetchBase64PdfWithSpecificPage, resetPdf } = usePdf();
  const { fetchText, resetText } = usePlainText();

  const handleReferenceClick = async (reference: ContextType) => {
    if (isPdfFileType(reference.file_type)) {
      resetText(); // テキストビューワーをリセット
      await fetchBase64PdfWithSpecificPage(reference, reference.page);
    } else {
      resetPdf(); // PDFビューワーをリセット
      await fetchText(reference);
    }
  };

  return (
    <>
      <div className="mt-3">
        <Accordion title="Reference">
          {props.references.map((reference, index) => (
            <div
              key={index}
              className="flex flex-col py-3 cursor-pointer"
              onClick={() => handleReferenceClick(reference)}
            >
              <h4 className="text-action-blue hover:underline cursor-pointer text-left">
                {reference.title}
              </h4>
              <p className="text-sm mt-2">{reference.chunk}</p>
            </div>
          ))}
        </Accordion>
      </div>
    </>
  );
};
