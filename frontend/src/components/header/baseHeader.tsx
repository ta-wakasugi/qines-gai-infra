"use client";
import Logo from "@/components/icons/logo";
import { UserIcon } from "@/components/icons/userIcon";
import { DISPLAY_PATH } from "@/consts/paths";
import { usePanelDisplay } from "@/hooks/collection/usePanelDisplay";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useState } from "react";
import { PanelOffIcon } from "../icons/panelOffIcon";
import { PanelOnIcon } from "../icons/panelOnIcon";
import UserMenu from "./userMenu";

/**
 * ベースヘッダーのカスタムフック
 * @returns ヘッダーの状態と操作関数を含むオブジェクト
 */
const useBaseHeader = () => {
  const { isPanelDisplay, togglePanelDisplay } = usePanelDisplay();
  const { commonButtonDisabled } = useButtonDisabled();
  const [isOpenMenu, setIsOpenMenu] = useState(false);
  const handleShowMenu = () => {
    setIsOpenMenu(true);
  };
  const handleCloseMenu = () => {
    setIsOpenMenu(false);
  };
  return {
    isPanelDisplay,
    togglePanelDisplay,
    commonButtonDisabled,
    isOpenMenu,
    handleShowMenu,
    handleCloseMenu,
  };
};

type HooksType = ReturnType<typeof useBaseHeader>;

type Props = {
  isPanelDisplay?: boolean;
};

/**
 * ベースヘッダーのビューコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns ヘッダーのJSX要素
 */
const BaseHeaderView = ({ props, hooks }: { props: Props; hooks: HooksType }) => {
  /**
   * パネルアイコンコンポーネント
   * @returns パネルの状態に応じたアイコンのJSX要素
   */
  const PanelIcon = () => {
    if (!props.isPanelDisplay) {
      return null;
    }
    if (hooks.isPanelDisplay) {
      return <PanelOnIcon className="ml-3 mt-1 w-5 h-5" />;
    }
    return <PanelOffIcon className="ml-3 mt-1 w-5 h-5" />;
  };
  return (
    <>
      <header className="relative flex justify-between items-center">
        <div className="w-1/2 flex items-end bg-opacity-100 h-[40px]">
          <div className="flex mt-2 ml-2">
            <Logo />
            <button onClick={hooks.togglePanelDisplay}>
              <PanelIcon />
            </button>
          </div>
          <nav className="ml-7 mb-1 space-x-5">
            <a
              className="text-blue-600 hover:underline"
              href={hooks.commonButtonDisabled ? "" : DISPLAY_PATH.ROOT}
            >
              TOP
            </a>
            <a
              className="text-blue-600 hover:underline"
              href={hooks.commonButtonDisabled ? "" : DISPLAY_PATH.COLLECTION.LIST}
            >
              COLLECTION
            </a>
          </nav>
        </div>
        <>
          <div className="w-1/2 flex justify-end py-2 bg-opacity-100 h-[40px]">
            <UserIcon
              className="mr-2 w-6 h-6 cursor-pointer"
              onClick={hooks.handleShowMenu}
            />
          </div>
          {hooks.isOpenMenu && (
            <UserMenu isOpen={hooks.isOpenMenu} onClose={hooks.handleCloseMenu} />
          )}
        </>
      </header>
    </>
  );
};

/**
 * ベースヘッダーのメインコンポーネント
 * @param isPanelDisplay - パネル表示フラグ（デフォルト: false）
 * @returns ヘッダーのJSX要素
 */
const BaseHeader = ({ isPanelDisplay = false }: Props) => {
  const hooks = useBaseHeader();
  return <BaseHeaderView props={{ isPanelDisplay }} hooks={hooks} />;
};

export default BaseHeader;
