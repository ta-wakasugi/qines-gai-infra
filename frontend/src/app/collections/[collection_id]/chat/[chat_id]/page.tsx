"use server";

import ConversationPage from "@/components/conversation/conversationPage";

type Props = {
  collection_id: string;
  chat_id: string;
};

/**
 * 既存チャット画面のコンポーネント
 * 指定されたチャットの会話履歴を表示し、会話を継続する
 * @param params - URLパラメータ（collection_id, chat_id）を含むオブジェクト
 * @returns JSX.Element
 */
export default async function Chat({ params }: { params: Props }) {
  const props = {
    collectionId: params.collection_id,
    chatId: params.chat_id,
  };
  return <ConversationPage props={props} />;
}
