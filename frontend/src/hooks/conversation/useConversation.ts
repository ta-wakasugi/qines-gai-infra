import { atom, useAtom } from "jotai";

const conversationIdAtom = atom<string | null>(null);

/**
 * 会話IDを管理するカスタムフック
 * @returns {Object} 会話IDの状態と操作関数を含むオブジェクト
 * @property {string | null} conversationId - 現在の会話ID
 * @property {Function} setConversationId - 会話IDを設定する関数
 */
export const useConversation = () => {
  const [conversationId, setConversationId] = useAtom(conversationIdAtom);

  return {
    conversationId,
    setConversationId,
  };
};
