"use client";
import { ArtifactType, ChatRequestType, StreamChatType } from "@/models/conversation";

/**
 * APIにチャットリクエストを送信し、ストリーミングレスポンスを処理します
 * @param params - チャットリクエストのパラメータ
 * @param updateStreamingMessage - ストリーミングメッセージを更新するためのコールバック関数
 * @param setArtifact - ストリーミングArtifactを更新するためのコールバック関数
 * @param addArtifactHistory - ストリーミングArtifactHistoryを更新するためのコールバック関数
 * @returns Promise<StreamChatType> - ストリームからの最終レスポンス
 * @throws APIルートが利用できない場合にエラーをスローします
 */
export const postConversation = async (
  params: ChatRequestType,
  updateStreamingMessage: (chunk: string) => void,
  setArtifact: (artifact: ArtifactType) => void,
  addArtifactHistory: (artifact: ArtifactType) => void
): Promise<StreamChatType> => {
  updateStreamingMessage("..."); // 送信中の表示(チャット中のローディング表示)
  const url = "/api/conversation";
  // NOTE:ストリーミング形式でServerコンポーネントからレスポンスを受け取るにはAPI Routesを利用する
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(params),
  });

  if (!response?.body) {
    throw new Error("route api error");
  }

  const reader = (response.body as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();
  let done = false;
  const responseChat: StreamChatType = {
    public_conversation_id: "",
    message: {
      role: "assistant",
      content: "",
      metadata: {
        version: "",
        contexts: null,
        recommended_documents: null,
        generated_artifacts: null,
      },
    },
    artifact: null,
  };
  const DATA_CHECK_KEYS = ["contexts", "recommended_documents", "generated_artifacts"];
  let responseContent = "";
  let artifactContent = "";
  let responseArtifact = null;
  let buffer = "";
  let current_artifact_id = "";
  let current_artifact_version = 0;

  while (!done) {
    const { value, done: readerDone } = await reader.read();
    done = readerDone;

    if (value) {
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line === "") continue;
        const lineToProcess = buffer + line;
        try {
          const streamJson = JSON.parse(lineToProcess);
          buffer = "";
          responseChat.public_conversation_id = streamJson.public_conversation_id;
          responseChat.message.role = streamJson.message.role;
          responseChat.message.metadata.version = streamJson.message.metadata.version;
          for (const metadataKey of DATA_CHECK_KEYS) {
            if (
              streamJson.message.metadata[metadataKey] &&
              Array.isArray(streamJson.message.metadata[metadataKey]) &&
              streamJson.message.metadata[metadataKey].length > 0
            ) {
              responseChat.message.metadata[metadataKey] =
                streamJson.message.metadata[metadataKey];
            }
          }
          if (streamJson.message.content !== "") {
            responseContent += streamJson.message.content;
            updateStreamingMessage(responseContent);
          }
          if (streamJson.artifact) {
            if (
              streamJson.artifact.id == current_artifact_id &&
              streamJson.artifact.version == current_artifact_version
            ) {
              artifactContent += streamJson.artifact.content;
            } else {
              addArtifactHistory(responseArtifact);
              artifactContent = streamJson.artifact.content;
              current_artifact_id = streamJson.artifact.id;
              current_artifact_version = streamJson.artifact.version;
            }
            responseArtifact = streamJson.artifact;
            responseArtifact.content = artifactContent;
            setArtifact(responseArtifact);
          }
        } catch (error) {
          buffer = lineToProcess;
        }
      }
      responseChat.message.content = responseContent;
      if (responseArtifact) {
        responseChat.artifact = responseArtifact;
      }
    }
  }
  return responseChat;
};
