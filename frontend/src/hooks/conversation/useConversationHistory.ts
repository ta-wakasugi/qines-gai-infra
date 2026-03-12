import { MessageType } from "@/models/conversation";
import { atom, useAtom } from "jotai";

const conversationHistoryAtom = atom<MessageType[]>([]);

/**
 * 会話履歴を管理するカスタムフック
 * @returns {Object} 会話履歴の状態と操作関数を含むオブジェクト
 * @property {MessageType[]} conversationHistory - 会話履歴リスト
 * @property {Function} setConversationHistory - 会話履歴を直接設定する関数
 * @property {Function} addConversationHistory - 会話履歴にメッセージを追加する関数
 * @property {Function} removeLastConversationHistory - 最後の会話履歴を削除する関数
 */
export const useConversationHistory = () => {
  const [conversationHistory, setConversationHistory] = useAtom(
    conversationHistoryAtom
  );

  /**
   * 会話履歴にメッセージを追加する
   * @param message - 追加するメッセージまたはメッセージ配列
   */
  const addConversationHistory = (message: MessageType | MessageType[]) => {
    if (Array.isArray(message)) {
      setConversationHistory((prev) => [...prev, ...message]);
    } else {
      setConversationHistory((prev) => [...prev, message]);
    }
  };

  /**
   * 会話履歴の最後のメッセージを削除する
   */
  const removeLastConversationHistory = () => {
    setConversationHistory((prev) => prev.slice(0, -1));
  };

  return {
    conversationHistory,
    setConversationHistory,
    addConversationHistory,
    removeLastConversationHistory,
  };
};
