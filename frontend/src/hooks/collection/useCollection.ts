import { CollectionDetailType } from "@/models/collection";
import { atom, useAtom } from "jotai";

const collectionAtom = atom<CollectionDetailType | null>(null);

/**
 * コレクションの状態を管理するカスタムフック
 * @returns {Object} コレクションの状態と操作関数を含むオブジェクト
 * @property {CollectionDetailType | null} collection - 現在のコレクション
 * @property {Function} setCollection - コレクションを設定する関数
 * @property {Function} getDocumentIds - コレクション内の全ドキュメントIDを取得する関数
 */
export const useCollection = () => {
  const [collection, setCollection] = useAtom(collectionAtom);

  /**
   * コレクション内の全ドキュメントIDを取得する
   * @returns ドキュメントIDの配列
   */
  const getDocumentIds = () => {
    return collection?.documents.map((doc) => doc.id) || [];
  };

  return {
    collection,
    setCollection,
    getDocumentIds,
  };
};
