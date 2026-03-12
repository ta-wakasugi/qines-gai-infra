"use client";
import { useRecommendDocuments } from "@/hooks/conversation/useRecommendDocuments";
import RecommendDocumentCard from "../document/card/recommendDocumentCard";

/**
 * おすすめドキュメントのリストを表示するコンポーネント
 * @returns {JSX.Element | null} おすすめドキュメントの一覧、またはnull
 */
export const RecommendDocuments = () => {
  const { recommendDocuments } = useRecommendDocuments();
  if (!recommendDocuments) {
    return null;
  }
  return (
    <>
      <div className="flex items-start gap-5 self-stretch w-11/12 flex-[0_0_auto] justify-self-center">
        <div className="flex-col items-start gap-3 p-3 flex-1 grow bg-[#ffffffcc] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f] w-4/5">
          <h3 className="ml-1 mb-2">Recommended</h3>
          {recommendDocuments.map((document, index) => (
            <RecommendDocumentCard
              key={index}
              document={document}
              className="w-full justify-self-center mb-3"
            />
          ))}
        </div>
      </div>
    </>
  );
};
