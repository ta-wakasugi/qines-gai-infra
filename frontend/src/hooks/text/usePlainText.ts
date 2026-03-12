import { getText } from "@/actions/text";
import { ContextType } from "@/models/conversation";
import { DocumentType } from "@/models/document";
import { atom, useAtom } from "jotai";

const DOCUMENT_ORIGIN =
  process.env.NEXT_PUBLIC_DOCUMENT_ORIGIN || "http://host.docker.internal:3000";

const textTitleAtom = atom<string | null>(null);
const textContentAtom = atom<string | null>(null);

/**
 * テキストビューアーの状態を管理するカスタムフック
 * @returns テキストビューアーの状態と操作関数を含むオブジェクト
 */
export const usePlainText = () => {
  const [textTitle, setTextTitle] = useAtom(textTitleAtom);
  const [textContent, setTextContent] = useAtom(textContentAtom);

  /**
   * テキストファイルを取得し、内容を保存する
   * @param document - 取得対象のドキュメントまたはコンテキスト
   */
  const fetchText = async (document: DocumentType | ContextType) => {
    try {
      setTextTitle(document.title);
      const path = DOCUMENT_ORIGIN + document.path;
      const content = await getText(path);
      setTextContent(content);
    } catch (error) {
      console.error("テキスト取得エラー:", error);
      setTextContent("ファイルの読み込みに失敗しました。");
      throw error;
    }
  };

  /**
   * テキストビューアーの状態をリセットする
   */
  const resetText = () => {
    setTextTitle(null);
    setTextContent(null);
  };

  return {
    textTitle,
    textContent,
    fetchText,
    resetText,
  };
};
