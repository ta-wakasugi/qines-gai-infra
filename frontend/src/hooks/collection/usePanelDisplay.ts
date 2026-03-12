import { atom, useAtom } from "jotai";

const isPanelDisplayAtom = atom<boolean>(true);

/**
 * パネル表示の状態を管理するカスタムフック
 * @returns {Object} パネル表示の状態と操作関数を含むオブジェクト
 * @property {boolean} isPanelDisplay - パネルの表示状態
 * @property {Function} togglePanelDisplay - パネル表示を切り替える関数
 */
export const usePanelDisplay = () => {
  const [isPanelDisplay, setIsPanelDisplay] = useAtom(isPanelDisplayAtom);

  /**
   * パネル表示の状態を切り替える
   */
  const togglePanelDisplay = () => {
    setIsPanelDisplay((prev) => !prev);
  };
  return {
    isPanelDisplay,
    togglePanelDisplay,
  };
};
