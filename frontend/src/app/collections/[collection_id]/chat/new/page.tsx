"use server";

import ConversationPage from "@/components/conversation/conversationPage";

type Props = {
  collection_id: string;
};

/**
 * 新規チャット画面のコンポーネント
 * 指定されたコレクションに対する新規チャットを開始する
 * @param params - URLパラメータ（collection_id）を含むオブジェクト
 * @returns JSX.Element
 */
export default async function Chat({ params }: { params: Props }) {
  const props = {
    collectionId: params.collection_id,
  };
  return <ConversationPage props={props} />;
}
