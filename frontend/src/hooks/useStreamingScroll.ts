"use client";
import { useEffect, useRef } from "react";

/**
 * ストリーミング中のスクロールを管理するカスタムフック
 * @param {string} message - ストリーミングメッセージ
 * @returns {object} スクロールコンテナの参照
 * @returns {React.MutableRefObject<HTMLDivElement>} scrollContainerRef - スクロールコンテナの参照
 */
export const useStreamingScroll = (message: string) => {
  const shouldAutoScrollRef = useRef(true);
  const currentScrollTop = useRef(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  /**
   * 最下部までスクロールする
   */
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) return;

    if (shouldAutoScrollRef.current) {
      scrollToBottom();
    }
    if (!message) {
      shouldAutoScrollRef.current = true;
    }

    /**
     * スクロールイベントのハンドラ
     */
    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
      // ユーザーが手動でスクロールしている場合(ストリーミング中に上向きへスクロールした場合と判定)
      if (message && scrollTop < currentScrollTop.current) {
        shouldAutoScrollRef.current = false;
      }
      currentScrollTop.current = scrollTop;
      // ユーザーが一番下までスクロールした場合
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 20;
      if (!shouldAutoScrollRef.current && isAtBottom) {
        shouldAutoScrollRef.current = true;
      }
    };
    scrollContainer.addEventListener("scroll", handleScroll);
    return () => scrollContainer.removeEventListener("scroll", handleScroll);
  }, [message]);

  return {
    scrollContainerRef,
  };
};
