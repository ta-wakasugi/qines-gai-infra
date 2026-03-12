import { CheckboxInput } from "@/components/input/checkboxInput";
import { useSearchCollectionDocuments } from "@/hooks/collection/document/useSearchCollectionDocuments";
import { CATEGORY_MAPPING, CheckboxCategory, CheckboxState } from "@/models/document";
import { useEffect, useRef } from "react";
import { BasePopupMenu } from "../popupMenu/basePopupMenu";

type Props = {
  isVisible: boolean;
  onClose: () => void;
};

/**
 * ドキュメント検索フィルターのカスタムフック
 * @param props - フィルターコンポーネントのプロパティ
 * @returns フィルターの状態と操作関数を含むオブジェクト
 */
const useDocumentSearchFilter = (props: Props) => {
  const { checkboxState, setCheckboxState, searchDocuments } =
    useSearchCollectionDocuments();
  const ref = useRef<HTMLDivElement>(null);

  /**
   * チェックボックスの個別選択・解除を処理する関数
   * @param category - チェックボックスのカテゴリ
   * @param value - チェックボックスの値
   */
  const toggleCheckbox = (category: CheckboxCategory, value: string) => {
    setCheckboxState((prev) => {
      const currentValues = prev[category];
      const newValues = currentValues.includes(value)
        ? currentValues.filter((item) => item !== value)
        : [...currentValues, value];
      return {
        ...prev,
        [category]: newValues,
      };
    });
  };

  /**
   * チェックボックスの一括選択・一括解除を処理する関数
   * @param category - チェックボックスのカテゴリ
   */
  const toggleAllCheckbox = (category: CheckboxCategory) => {
    setCheckboxState((prev) => {
      const categoryItems = CATEGORY_MAPPING[category].items;
      const newValues = isAllSelected(category) ? [] : [...categoryItems];
      return {
        ...prev,
        [category]: newValues,
      };
    });
  };

  /**
   * カテゴリーの全項目が選択されているかを確認する関数
   * @param category - チェックボックスのカテゴリ
   * @returns すべての項目が選択されている場合はtrue
   */
  const isAllSelected = (category: CheckboxCategory): boolean => {
    return checkboxState[category].length === CATEGORY_MAPPING[category].items.length;
  };

  useEffect(() => {
    searchDocuments();
  }, [checkboxState]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        props.onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
  }, [props]);

  return {
    ref,
    checkboxState,
    toggleCheckbox,
    toggleAllCheckbox,
    isAllSelected,
  };
};

type Hooks = ReturnType<typeof useDocumentSearchFilter>;

type CheckboxGroupProps = {
  category: CheckboxCategory;
  categoryOptions: (typeof CATEGORY_MAPPING)[keyof typeof CATEGORY_MAPPING];
  checkboxState: CheckboxState;
  isAllSelected: (category: CheckboxCategory) => boolean;
  toggleAllCheckbox: (category: CheckboxCategory) => void;
  toggleCheckbox: (category: CheckboxCategory, value: string) => void;
};

/**
 * チェックボックスグループコンポーネント
 * @param props - チェックボックスグループのプロパティ
 * @returns チェックボックスグループのJSX要素
 */
const CheckboxGroup = ({
  category,
  categoryOptions,
  checkboxState,
  isAllSelected,
  toggleAllCheckbox,
  toggleCheckbox,
}: CheckboxGroupProps) => (
  <div className="flex-col w-40 items-start flex">
    <div className="items-center gap-2.5 px-2 py-3 w-full flex">
      <CheckboxInput
        checked={isAllSelected(category)}
        onClick={() => toggleAllCheckbox(category)}
        label={categoryOptions.title}
      />
      <div className="[font-family:'Noto_Sans-Bold',Helvetica] font-bold text-pale-blue text-xs">
        {categoryOptions.title}
      </div>
    </div>

    {categoryOptions.items.map((item) => (
      <div
        className="inline-flex items-center gap-2.5 px-2 py-1 w-full border-b"
        key={item}
      >
        <CheckboxInput
          checked={checkboxState[category].includes(item)}
          onClick={() => toggleCheckbox(category, item)}
          label={item}
        />
        <div className="[font-family:'Noto_Sans-Bold',Helvetica] ">{item}</div>
      </div>
    ))}
  </div>
);

/**
 * ドキュメント検索フィルターのビューコンポーネント
 * @param props - フィルターコンポーネントのプロパティ
 * @param hooks - カスタムフックの戻り値
 * @returns フィルターのJSX要素
 */
const DocumentSearchFilterView = ({ props, hooks }: { props: Props; hooks: Hooks }) => {
  if (!props.isVisible) {
    return null;
  }

  return (
    <BasePopupMenu
      className="top-14 right-16"
      isVisible={props.isVisible}
      onClose={props.onClose}
    >
      {(
        Object.entries(CATEGORY_MAPPING) as [
          CheckboxCategory,
          (typeof CATEGORY_MAPPING)[keyof typeof CATEGORY_MAPPING],
        ][]
      ).map(([category, categoryOptions]) => (
        <CheckboxGroup
          key={category}
          categoryOptions={categoryOptions}
          category={category}
          checkboxState={hooks.checkboxState}
          isAllSelected={hooks.isAllSelected}
          toggleAllCheckbox={hooks.toggleAllCheckbox}
          toggleCheckbox={hooks.toggleCheckbox}
        />
      ))}
    </BasePopupMenu>
  );
};

/**
 * ドキュメント検索フィルターのメインコンポーネント
 * @param props - フィルターコンポーネントのプロパティ
 * @returns フィルターのJSX要素
 */
export const DocumentSearchFilter = (props: Props) => {
  const hooks = useDocumentSearchFilter(props);
  return <DocumentSearchFilterView props={props} hooks={hooks} />;
};
