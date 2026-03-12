import { RecommendDocumentType } from "@/models/conversation";
import { atom, useAtom } from "jotai";

const recommendDocumentsAtom = atom<RecommendDocumentType | null>(null);

/**
 * レコメンドされたドキュメントを管理するカスタムフック
 * @returns {Object} レコメンドドキュメントの状態と操作関数を含むオブジェクト
 * @property {RecommendDocumentType | null} recommendDocuments - レコメンドされたドキュメントリスト
 * @property {Function} setRecommendDocuments - レコメンドドキュメントを設定する関数
 * @property {Function} deleteRecommendDocument - 指定IDのドキュメントを削除する関数
 */
export const useRecommendDocuments = () => {
  const [recommendDocuments, setRecommendDocuments] = useAtom(recommendDocumentsAtom);

  /**
   * 指定されたIDのドキュメントを削除する
   * @param documentId - 削除対象のドキュメントID
   */
  const deleteRecommendDocument = (documentId: string) => {
    if (!recommendDocuments) {
      return;
    }
    // 全Documentを削除する場合リコメンド枠自体を削除するためNullを設定
    if (recommendDocuments.length === 1) {
      setRecommendDocuments(null);
      return;
    }
    const documents = recommendDocuments.filter(
      (document) => document.id !== documentId
    );
    setRecommendDocuments(documents);
  };

  return {
    recommendDocuments,
    setRecommendDocuments,
    deleteRecommendDocument,
  };
};
