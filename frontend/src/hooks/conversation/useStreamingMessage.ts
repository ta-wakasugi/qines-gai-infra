import { atom, useAtom } from "jotai";

const streamingMessageAtom = atom<string>("");

/**
 * ストリーミングメッセージを管理するカスタムフック
 * @returns {Object} ストリーミングメッセージの状態と操作関数を含むオブジェクト
 * @property {string} streamingMessage - 現在のストリーミングメッセージ
 * @property {Function} setStreamingMessage - ストリーミングメッセージを更新する関数
 */
export const useStreamingMessage = () => {
  const [streamingMessage, setStreamingMessage] = useAtom(streamingMessageAtom);
  return {
    streamingMessage,
    setStreamingMessage,
  };
};
