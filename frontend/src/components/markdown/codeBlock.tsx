import mermaid from "mermaid";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { getCodeString } from "rehype-rewrite";

interface Props {
  children?: React.ReactNode[];
  className?: string;
  node?: {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    children: any[];
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

/**
 * ランダムなIDを生成する
 * @returns {string} ランダムなID
 */
const randomid = (): string => parseInt(String(Math.random() * 1e15), 10).toString(36);

/**
 * コードブロックを表示するコンポーネント
 * Mermaid図の描画にも対応
 * @param {Props} props - コンポーネントのプロパティ
 * @returns {JSX.Element} コードブロック要素
 */
const CodeBlock = ({ children = [], className, ...props }: Props) => {
  const demoid = useRef<string>(`dome${randomid()}`);
  const [container, setContainer] = useState<HTMLElement | null>(null);
  const isMermaid =
    className && /^language-mermaid/.test(className.toLocaleLowerCase());
  const code =
    props.node && props.node.children
      ? getCodeString(props.node.children)
      : children[0] || "";

  const reRender = async (): Promise<void> => {
    if (container && isMermaid) {
      try {
        const config = {
          suppressErrorRendering: true,
        };
        mermaid.initialize(config);
        const str = await mermaid.render(demoid.current, String(code));
        container.innerHTML = str.svg;
      } catch (error) {
        container.innerHTML = error instanceof Error ? error.message : String(error);
      }
    }
  };

  useEffect(() => {
    reRender();
  }, [container, isMermaid, code, demoid]);

  const refElement = useCallback((node: HTMLElement | null) => {
    if (node !== null) {
      setContainer(node);
    }
  }, []);

  if (isMermaid) {
    return (
      <Fragment>
        <code id={demoid.current} style={{ display: "none" }} />
        <code ref={refElement} data-name="mermaid" />
      </Fragment>
    );
  }

  const isLanguage = className && /^language-/.test(className.toLocaleLowerCase());
  if (!isLanguage) {
    return <code>{children}</code>;
  }

  return (
    <div className="scroll-container">
      <code>{children}</code>
    </div>
  );
};

export default CodeBlock;
