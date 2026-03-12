import { act, renderHook } from "@testing-library/react";
import { usePdfViewer } from "./pdfViewer";

jest.mock("react-pdf", () => ({
  Document: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Page: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  pdfjs: {
    GlobalWorkerOptions: {
      workerSrc: "",
    },
    getDocument: () => {
      return {
        promise: Promise.resolve({
          numPages: 1,
          getPage: () => ({ getViewport: () => ({ width: 1, height: 1 }) }),
        }),
      };
    },
  },
}));

describe("pdfViewer", () => {
  describe("usePdfViewer", () => {
    it("dataUrlはPDF指定の文字列となっていること", async () => {
      let result: any; // eslint-disable-line @typescript-eslint/no-explicit-any
      await act(async () => {
        const hooks = renderHook(() => usePdfViewer());
        result = hooks.result;
      });
      expect(result.current.dataUrl).toBe("data:application/pdf;base64,null");
    });

    describe("jumpToPage", () => {
      it("フォームの値を取得し、pdfRef.current.scrollToIndexを呼び出す", async () => {
        const scrollToIndex = jest.fn();
        const formElement = document.createElement("form");
        const formInput = document.createElement("input");
        formInput.name = "value";
        formInput.value = "1";
        formElement.appendChild(formInput);
        const e = {
          currentTarget: formElement,
          preventDefault: () => jest.fn(),
        } as unknown as React.FormEvent<HTMLFormElement>;

        let result: any; // eslint-disable-line @typescript-eslint/no-explicit-any
        await act(async () => {
          const hooks = renderHook(() => usePdfViewer());
          result = hooks.result;
        });
        result.current.ref.current = { scrollToIndex } as any; // eslint-disable-line @typescript-eslint/no-explicit-any
        result.current.jumpToPage(e);
        expect(scrollToIndex).toHaveBeenCalledWith({ index: 0 });
      });
    });

    describe("jumpToLink", () => {
      it("リンクのクリックイベントより、pdfRef.current.scrollToIndexを呼び出す", async () => {
        const scrollToIndex = jest.fn();
        const props = { dest: [], pageIndex: 1, pageNumber: 2 };
        const { result } = renderHook(() => usePdfViewer());

        /** @ts-expect-error insert mock function */
        result.current.ref.current = { scrollToIndex };
        result.current.jumpByLink(props);

        expect(scrollToIndex).toHaveBeenCalledWith({ index: 1 });
      });
    });

    describe("PdfMenu", () => {
      test.todo("zoomInが呼ばれる");
      test.todo("zoomOutが呼ばれる");
      test.todo("jumpToPageが呼ばれる");
      test.todo("resetPdfが呼ばれる");
    });
  });
  describe("pdfViewerLayout", () => {
    test.todo("閉じるボタン押下時にonCloseが1回呼ばれる");
    test.todo("ドキュメントが読み込まれた時にonDocumentLoadSuccessが1回呼ばれる");
  });
});
