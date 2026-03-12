"use client";

import { postChatStart } from "@/actions/conversation";
import HelpIcon from "@/components/icons/helpIcon";
import { SendIcon } from "@/components/icons/sendIcon";
import { DISPLAY_PATH, QUERY_PARAMS } from "@/consts/paths";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import { useLoading } from "@/hooks/useLoading";
import { ChatRequestBaseType } from "@/models/conversation";
import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * チャット開始入力フィールドのカスタムフック
 * @returns チャット開始入力の状態と操作関数を含むオブジェクト
 */
const useChatStartInput = () => {
  const router = useRouter();
  const [inputMessage, setInputMessage] = useState<string>("");
  const { commonButtonDisabled, setCommonButtonDisabled } = useButtonDisabled();
  const { showError, errorTemplate } = useError();
  const { showLoading, hideLoading } = useLoading();

  /**
   * チャット開始を処理する関数
   */
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    showLoading();
    setCommonButtonDisabled(true);
    const requestParams = {
      message: inputMessage,
    } as ChatRequestBaseType;
    try {
      const response = await postChatStart(requestParams);
      router.push(
        `${DISPLAY_PATH.CONVERSATION.NEW(response.public_collection_id)}?${QUERY_PARAMS.INITIAL_MESSAGE}=${encodeURIComponent(inputMessage)}`
      );
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
    } finally {
      setCommonButtonDisabled(false);
      hideLoading();
    }
  };

  return { commonButtonDisabled, inputMessage, setInputMessage, handleSubmit };
};

type ChatStartInputHooksType = ReturnType<typeof useChatStartInput>;

/**
 * チャット開始入力フィールドのビューコンポーネント
 * @param hooks - カスタムフックの戻り値
 * @returns チャット開始入力フィールドのJSX要素
 */
export const ChatStartInputView = ({ hooks }: { hooks: ChatStartInputHooksType }) => {
  return (
    <>
      <div className="inline-flex items-center gap-3 relative">
        <div className="[font-family:'Noto_Sans_JP-SemiBold',Helvetica] font-semibold text-3xl tracking-[1.20px] ">
          まずは聞いてみる
        </div>
        <div data-testid="helpIcon">
          <HelpIcon />
        </div>
      </div>

      <div className="flex top-8 h-16 items-center gap-2 p-4 py-6 relative self-stretch w-full bg-chat-area rounded-2xl border-2 border-solid border-white shadow-[0px_2px_12px_#aaaaaa1f]">
        <div className="relative w-full [font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal text-gray text-base tracking-[0.32px] whitespace-nowrap">
          <form onSubmit={hooks.handleSubmit}>
            <input
              className="w-11/12 p-2 outline-none bg-transparent"
              type="text"
              placeholder="タスクの内容を入力してください"
              value={hooks.inputMessage}
              onChange={(e) => hooks.setInputMessage(e.target.value)}
            />
            {/* TODO:　ボタンデザイン確認後に修正 */}
            <button
              className="w-1/12"
              type="submit"
              disabled={hooks.inputMessage === "" || hooks.commonButtonDisabled}
            >
              <div
                className="flex justify-end items-center py-3 mx-3"
                data-testid="sendIcon"
              >
                <SendIcon />
              </div>
            </button>
          </form>
        </div>
      </div>
    </>
  );
};

/**
 * チャット開始入力フィールドのメインコンポーネント
 * @returns チャット開始入力フィールドのJSX要素
 */
export const ChatStartInput = () => {
  const hooks = useChatStartInput();
  return <ChatStartInputView hooks={hooks} />;
};
