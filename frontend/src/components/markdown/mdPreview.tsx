import MarkdownPreview from "@uiw/react-markdown-preview";
import {
  ClassAttributes,
  ElementType,
  HTMLAttributes,
  TableHTMLAttributes,
} from "react";
import CodeBlock from "./codeBlock";
import TableBlock from "./tableBlock";
import "./mdPreview.css";

interface Props {
  source: string;
  className?: string;
}

/**
 * マークダウンプレビューを表示するコンポーネント
 * Mermaid図の描画に対応したマークダウンプレビューを提供
 * @param {Props} props - コンポーネントのプロパティ
 * @returns {JSX.Element} マークダウンプレビュー要素
 */

/**
 * マークダウンプレビューを表示するコンポーネント
 * Mermaid図の描画に対応したマークダウンプレビューを提供
 * @param {Props} props - コンポーネントのプロパティ
 * @returns {JSX.Element} マークダウンプレビュー要素
 */
const MdPreview = ({ source, className }: Props) => {
  return (
    <MarkdownPreview
      source={source}
      className={className}
      components={{
        code: CodeBlock as ElementType<
          ClassAttributes<HTMLElement> & HTMLAttributes<HTMLElement>
        >,
        table: TableBlock as ElementType<
          ClassAttributes<HTMLTableElement> & TableHTMLAttributes<HTMLTableElement>
        >,
      }}
    />
  );
};

export default MdPreview;
