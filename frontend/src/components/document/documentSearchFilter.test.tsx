import React from "react";
import { render, screen } from "@testing-library/react";
import { DocumentSearchFilter } from "./documentSearchFilter";
import { CATEGORY_MAPPING } from "@/models/document";
import userEvent from "@testing-library/user-event";

jest.mock("@/actions/document", () => ({
  searchDocument: jest.fn().mockResolvedValue({
    documents: [
      {
        id: "1",
        title: "title",
        genre: "genre",
        release: "release",
        path: "path",
        subject: "AUTOSAR",
        file_type: "application/pdf",
      },
    ],
  }),
}));

describe("DocumentSearchFilter", () => {
  const props = {
    isVisible: true,
    onClose: jest.fn(),
  };

  it("全てのチェックボックスが描画されること", () => {
    const { getByText, getByTestId } = render(<DocumentSearchFilter {...props} />);
    expect(getByTestId("popupMenu")).toBeInTheDocument();
    Object.values(CATEGORY_MAPPING).forEach((category) => {
      expect(getByText(category.title)).toBeInTheDocument();
      category.items.forEach((item) => {
        expect(getByText(item)).toBeInTheDocument();
      });
    });
  });

  it("isVisible=false時は表示されないこと", () => {
    render(<DocumentSearchFilter {...props} isVisible={false} />);
    expect(screen.queryByTestId("searchFilter")).not.toBeInTheDocument();
  });

  it("ポップアップの枠外をクリックしたら、onCloseが呼ばれること", async () => {
    const { container } = render(<DocumentSearchFilter {...props} />);
    await userEvent.click(container); // Click outside the popup
    expect(props.onClose).toHaveBeenCalled();
  });

  it("チェックボックスを個別選択・解除できること", async () => {
    const { getByLabelText } = render(<DocumentSearchFilter {...props} />);
    const genreCheckbox = getByLabelText(CATEGORY_MAPPING.genre.items[0]);
    await userEvent.click(genreCheckbox);
    expect(genreCheckbox).toHaveAttribute("aria-checked", "true");
    await userEvent.click(genreCheckbox);
    expect(genreCheckbox).toHaveAttribute("aria-checked", "false");
  });

  it("チェックボックスを一括選択・解除できること", async () => {
    const { getByLabelText } = render(<DocumentSearchFilter {...props} />);
    const genreAllCheckbox = getByLabelText(CATEGORY_MAPPING.genre.title);
    // 一括選択
    await userEvent.click(genreAllCheckbox);
    expect(genreAllCheckbox).toHaveAttribute("aria-checked", "true");
    Object.values(CATEGORY_MAPPING.genre.items).forEach((genre) => {
      expect(getByLabelText(genre)).toHaveAttribute("aria-checked", "true");
    });
    // 一括解除
    await userEvent.click(genreAllCheckbox);
    expect(genreAllCheckbox).toHaveAttribute("aria-checked", "false");
    Object.values(CATEGORY_MAPPING.genre.items).forEach((genre) => {
      expect(getByLabelText(genre)).toHaveAttribute("aria-checked", "false");
    });
  });
});
