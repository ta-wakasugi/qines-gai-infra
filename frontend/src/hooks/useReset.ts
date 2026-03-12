"use client";
import { useCollection } from "./collection/useCollection";
import { useArtifact } from "./conversation/useArtifact";
import { useConversation } from "./conversation/useConversation";
import { useConversationHistory } from "./conversation/useConversationHistory";
import { useRecommendDocuments } from "./conversation/useRecommendDocuments";
import { usePdf } from "./pdf/usePdf";
import { useButtonDisabled } from "./useButtonDisabled";
import { useDragDropUpload } from "./useDragDropUpload";
import { useError } from "./useError";

/**
 * 全てのカスタムフックの状態をリセットするカスタムフック
 * @returns {Object} リセット機能に関する値とメソッド
 * @property {Function} resetHooks - アプリケーションの全状態をリセットするメソッド
 *   以下の状態を初期値に戻します:
 *   - エラーメッセージを空にする
 *   - ボタンの無効化状態を解除する
 *   - 会話IDをnullにする
 *   - 会話履歴を空配列にする
 *   - おすすめドキュメントをnullにする
 *   - コレクションをnullにする
 *   - PDFの状態をリセットする
 *   - アーティファクトの状態をリセットする
 *   - 最新のアーティファクトをnullにする
 *   - アーティファクト履歴を空配列にする
 *   - アップロードファイルをnullにする
 */
export const useReset = () => {
  const { hiddenError } = useError();
  const { setCommonButtonDisabled } = useButtonDisabled();
  const { setConversationId } = useConversation();
  const { setConversationHistory } = useConversationHistory();
  const { setRecommendDocuments } = useRecommendDocuments();
  const { setCollection } = useCollection();
  const { resetPdf } = usePdf();
  const { resetArtifact, setLatestArtifact, setArtifactHistory } = useArtifact();
  const { setUploadFile } = useDragDropUpload();

  const resetHooks = () => {
    hiddenError();
    setCommonButtonDisabled(false);
    setConversationId(null);
    setConversationHistory([]);
    setRecommendDocuments(null);
    setCollection(null);
    resetPdf();
    resetArtifact();
    setLatestArtifact(null);
    setArtifactHistory([]);
    setUploadFile(null);
  };

  return {
    resetHooks,
  };
};
