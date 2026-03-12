import { act, renderHook } from "@testing-library/react";
import { useRecommendDocuments } from "./useRecommendDocuments";
import { RecommendDocumentType } from "@/models/conversation";

const testRecommendDocuments: RecommendDocumentType = [
  {
    id: "1",
    title: "Sample Document",
    path: "/sample-document.pdf",
    subject: "AUTOSAR",
    genre: "Sample Genre",
    release: "2023-10-01",
    file_type: "application/pdf",
  },
  {
    id: "2",
    title: "Sample Document2",
    path: "/sample-document2.pdf",
    subject: "AUTOSAR",
    genre: "Sample Genre2",
    release: "2023-10-02",
    file_type: "application/pdf",
  },
];

describe("useRecommendDocuments", () => {
  afterEach(() => {
    // jotaiの初期化
    const { result } = renderHook(() => useRecommendDocuments());
    act(() => {
      result.current.setRecommendDocuments(null);
    });
  });
  it("初期値はnullであること", () => {
    const { result } = renderHook(() => useRecommendDocuments());
    expect(result.current.recommendDocuments).toEqual(null);
  });
  it("会話の削除確認:nullの場合、エラーとならないこと", () => {
    const { result } = renderHook(() => useRecommendDocuments());
    act(() => {
      result.current.deleteRecommendDocument(1);
    });
    expect(result.current.recommendDocuments).toEqual(null);
  });
  it("会話の削除確認:複数のうち、１つだけ削除した場合", () => {
    const { result } = renderHook(() => useRecommendDocuments());
    act(() => {
      result.current.setRecommendDocuments(testRecommendDocuments);
    });
    act(() => {
      result.current.deleteRecommendDocument("2");
    });
    const expectDocuments = testRecommendDocuments.filter(
      (document) => document.id !== "2"
    );
    expect(expectDocuments).toEqual(result.current.recommendDocuments);
  });
  it("会話の削除確認:全削除の場合、nullとなること", () => {
    const { result } = renderHook(() => useRecommendDocuments());
    const setData = testRecommendDocuments.filter((document) => document.id !== "2");
    act(() => {
      result.current.setRecommendDocuments(setData);
    });
    act(() => {
      result.current.deleteRecommendDocument(0);
    });
    expect(result.current.recommendDocuments).toEqual(null);
  });
});
