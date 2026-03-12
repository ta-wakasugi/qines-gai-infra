export const DISPLAY_PATH = {
  ROOT: "/",
  COLLECTION: {
    NEW: "/collections/new",
    EDIT: (publicCollectionId: string) => `/collections/${publicCollectionId}`,
    LIST: "/collections",
  },
  CONVERSATION: {
    NEW: (publicCollectionId: string) => `/collections/${publicCollectionId}/chat/new`,
    CHAT: (publicCollectionId: string, chatId: string) =>
      `/collections/${publicCollectionId}/chat/${chatId}`,
  },
};
// リクエストパスのクエリパラメータを定義
export const QUERY_PARAMS = {
  INITIAL_MESSAGE: "initial_message",
};
