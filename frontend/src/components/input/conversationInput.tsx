"use client";

import { THEME_COLORS } from "@/consts/color";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { SendIcon } from "../icons/sendIcon";
import { useConversationInput } from "@/hooks/conversation/useConversationInput";

type Props = {
  collectionId: string;
};

/**
 * 会話入力フィールドのカスタムフック
 * @param props - コンポーネントのプロパティ
 * @returns 会話入力の状態と操作関数を含むオブジェクト
 */
const useHookConversationInput = (props: Props) => {
  const { inputMessage, setInputMessage, sendMessage } = useConversationInput();
  const { commonButtonDisabled } = useButtonDisabled();

  /**
   * メッセージ送信を処理する関数
   */
  const handleSubmit = async () => {
    sendMessage({ message: inputMessage, collectionId: props.collectionId });
  };

  /**
   * Ctrl(or Cmd) + EnterでFormを送信する
   * @param event - キーボードイベント
   */
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (commonButtonDisabled) return;
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      const form = document.getElementById("conversation-form") as HTMLFormElement;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  return {
    commonButtonDisabled,
    inputMessage,
    setInputMessage,
    handleSubmit,
    handleKeyDown,
  };
};

type ConversationInputHooksType = ReturnType<typeof useHookConversationInput>;

/**
 * 会話入力フィールドのビューコンポーネント
 * @param hooks - カスタムフックの戻り値
 * @returns 会話入力フィールドのJSX要素
 */
export const ConversationInputView = ({
  hooks,
}: {
  hooks: ConversationInputHooksType;
}) => {
  const sendButtonDisabled = Boolean(
    hooks.inputMessage === "" || hooks.commonButtonDisabled
  );
  const iconColor = sendButtonDisabled
    ? THEME_COLORS.buttonDisabled
    : THEME_COLORS.button;
  return (
    <>
      <form
        id="conversation-form"
        action={hooks.handleSubmit}
        className={`flex w-11/12 h-22 px-2 py-1 bg-chat-area rounded-2xl border-2 border-solid border-white shadow-[0px_2px_12px_#aaaaaa1f]`}
      >
        <div className="flex-grow my-1 bg-chat-area">
          <textarea
            className={`w-full resize-none outline-none pl-1 bg-[#fbfbfc]`}
            rows={3}
            value={hooks.inputMessage}
            onChange={(e) => hooks.setInputMessage(e.target.value)}
            onKeyDown={hooks.handleKeyDown}
          />
        </div>
        <button
          className="flex items-end mb-1"
          type="submit"
          disabled={sendButtonDisabled}
        >
          <SendIcon color={iconColor} className="ml-3 w-6" />
        </button>
      </form>
    </>
  );
};

/**
 * 会話入力フィールドのメインコンポーネント
 * @param props - コンポーネントのプロパティ
 * @returns 会話入力フィールドのJSX要素
 */
export const ConversationInput = (props: Props) => {
  const hooks = useHookConversationInput(props);
  return <ConversationInputView hooks={hooks} />;
};
