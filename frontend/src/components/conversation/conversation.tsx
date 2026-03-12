"use client";

import { useConversationHistory } from "@/hooks/conversation/useConversationHistory";
import { useStreamingMessage } from "@/hooks/conversation/useStreamingMessage";
import { ConversationInput } from "../input/conversationInput";
import { AgentMessage } from "./agentMessage";
import { ConversationHistory } from "./conversationHistory";
import { RecommendDocuments } from "./recommendDocuments";
import { useStreamingScroll } from "@/hooks/useStreamingScroll";

type Props = {
  collectionId: string;
};

/**
 * 会話画面のメインコンポーネント。
 * 会話履歴の表示、新規メッセージの入力、会話要約などの機能を提供する
 */
export const Conversation = ({ collectionId }: Props) => {
  const { conversationHistory } = useConversationHistory();
  const { streamingMessage } = useStreamingMessage();
  const { scrollContainerRef } = useStreamingScroll(streamingMessage);

  return (
    <>
      <div className="flex-1 overflow-y-auto" ref={scrollContainerRef}>
        <div className="grid flex-col items-start gap-4 self-stretch w-full mx-auto">
          {conversationHistory.map((data, index) => (
            <ConversationHistory key={index} conversation={data} />
          ))}
          <RecommendDocuments />
          {streamingMessage && (
            <AgentMessage message={streamingMessage} disabled={true} />
          )}
        </div>
      </div>
      {/* 入力送信部分 */}
      <div className="flex flex-col mt-3 mb-1 items-start gap-1 w-full">
        <div className="flex justify-center items-center gap-4 w-full mb-1">
          <ConversationInput collectionId={collectionId} />
        </div>
      </div>
    </>
  );
};
