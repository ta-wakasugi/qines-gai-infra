import { DocumentType } from "@/models/document";
import { ReactNode, RefObject } from "react";

interface Props {
  className: string;
  document: DocumentType;
  CardCategoryArea?: ReactNode;
  DocumentIcon?: ReactNode;
  OpenDocumentIcon?: ReactNode;
  AddDocumentIcon?: ReactNode;
  CloseIcon?: ReactNode;
  dragRef?: RefObject<HTMLDivElement>;
  isVerticalButtons?: boolean;
}

/**
 * ベースドキュメントカードコンポーネント
 * @param props - カードのプロパティ
 * @param props.className - スタイルクラス名
 * @param props.document - ドキュメント情報
 * @param props.CardCategoryArea - カテゴリー表示エリアのコンポーネント
 * @param props.DocumentIcon - ドキュメントアイコンのコンポーネント
 * @param props.OpenDocumentIcon - ドキュメントを開くボタンのコンポーネント
 * @param props.AddDocumentIcon - ドキュメント追加ボタンのコンポーネント
 * @param props.CloseIcon - 閉じるボタンのコンポーネント
 * @param props.dragRef - ドラッグ＆ドロップ用の参照
 * @param props.isVerticalButtons - ボタンを垂直配置するかどうか
 * @returns ドキュメントカードのJSX要素
 */
const BaseDocumentCard = (props: Props) => {
  const {
    className,
    document,
    CardCategoryArea,
    OpenDocumentIcon,
    DocumentIcon,
    AddDocumentIcon,
    CloseIcon,
    dragRef,
    isVerticalButtons = false,
  } = props;

  return (
    <div
      ref={dragRef}
      className={`flex flex-col items-start gap-1 rounded-2xl ${className}`}
    >
      <div
        className={`flex flex-col items-start shadow-[0px_2px_12px_#aaaaaa1f] bg-[#ffffffcc] w-full self-stretch px-3 py-2 rounded-2xl`}
      >
        <div
          className={`w-full flex self-stretch flex-[0_0_auto] flex-col items-end gap-1`}
        >
          <div className="flex w-full self-stretch items-center h-7 justify-between">
            <div className="flex items-center w-3/4 flex-grow">
              <div>{DocumentIcon}</div>
              <div
                className="ml-2 text-ellipsis overflow-hidden whitespace-nowrap grow"
                title={document.title}
              >
                {document.title}
              </div>
              {isVerticalButtons && <div className="ml-1 mt-2">{CloseIcon}</div>}
            </div>
            {!isVerticalButtons && (
              <div className="ml-1 mt-2 flex">
                {CloseIcon}
                {OpenDocumentIcon}
              </div>
            )}
          </div>
          <div className="flex w-full items-center justify-between">
            <div className="flex items-center flex-grow min-h-[2.875rem]">
              <div className="grow">{CardCategoryArea}</div>
              {isVerticalButtons && <div className="py-1">{OpenDocumentIcon}</div>}
            </div>
          </div>
        </div>
        {AddDocumentIcon}
      </div>
    </div>
  );
};

export default BaseDocumentCard;
