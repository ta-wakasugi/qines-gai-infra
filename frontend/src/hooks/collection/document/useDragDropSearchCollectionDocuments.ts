import { DRAG_ITEM_TYPES } from "@/consts/draggable";
import { DocumentType } from "@/models/document";
import { useRef } from "react";
import { useDrag, useDrop } from "react-dnd";
import { useSearchCollectionDocuments } from "./useSearchCollectionDocuments";

/**
 * 検索結果のドキュメントをドラッグするためのカスタムフック
 * @param {DocumentType} document - ドラッグ対象のドキュメント
 * @returns {Object} ドラッグ機能を含むオブジェクト
 * @property {React.RefObject<HTMLDivElement>} dragRef - ドラッグ要素の参照
 * @property {boolean} isDragging - ドラッグ中かどうかを示すフラグ
 */
export const useSearchedDocumentDrag = (document: DocumentType) => {
  const dragRef = useRef<HTMLDivElement>(null);
  const [{ isDragging }, drag] = useDrag(
    {
      type: DRAG_ITEM_TYPES.SEARCHED_DOCUMENT,
      item: document,
      collect: (monitor) => ({
        isDragging: monitor.isDragging(),
      }),
    },
    [document]
  );
  drag(dragRef);
  return { dragRef, isDragging };
};

/**
 * コレクションエリアにドキュメントをドロップするためのカスタムフック
 * @returns {Object} ドロップ機能を含むオブジェクト
 * @property {React.RefObject<HTMLDivElement>} dropRef - ドロップ要素の参照
 */
export const useCollectionDocumentDrop = () => {
  const { moveToCollection } = useSearchCollectionDocuments();
  const dropRef = useRef<HTMLDivElement>(null);
  const [, drop] = useDrop({
    accept: DRAG_ITEM_TYPES.SEARCHED_DOCUMENT,
    drop: (item: DocumentType) => {
      moveToCollection(item);
    },
  });
  drop(dropRef);
  return { dropRef };
};

/**
 * コレクション内のドキュメントをドラッグするためのカスタムフック
 * @param {DocumentType} document - ドラッグ対象のドキュメント
 * @returns {Object} ドラッグ機能を含むオブジェクト
 * @property {React.RefObject<HTMLDivElement>} dragRef - ドラッグ要素の参照
 * @property {boolean} isDragging - ドラッグ中かどうかを示すフラグ
 */
export const useCollectionDocumentDrag = (document: DocumentType) => {
  const dragRef = useRef<HTMLDivElement>(null);
  const [{ isDragging }, drag] = useDrag(
    {
      type: DRAG_ITEM_TYPES.COLLECTION_DOCUMENT,
      item: document,
      collect: (monitor) => ({
        isDragging: monitor.isDragging(),
      }),
    },
    [document]
  );
  drag(dragRef);
  return { dragRef, isDragging };
};

/**
 * 検索エリアにドキュメントをドロップするためのカスタムフック
 * @returns {Object} ドロップ機能を含むオブジェクト
 * @property {React.RefObject<HTMLDivElement>} dropRef - ドロップ要素の参照
 */
export const useSearchedDocumentDrop = () => {
  const { removeFromCollection } = useSearchCollectionDocuments();
  const dropRef = useRef<HTMLDivElement>(null);
  const [, drop] = useDrop({
    accept: DRAG_ITEM_TYPES.COLLECTION_DOCUMENT,
    drop: (item: DocumentType) => {
      removeFromCollection(item);
    },
  });
  drop(dropRef);
  return { dropRef };
};
