import { render } from "@testing-library/react";
import { BasePopupMenu } from "./basePopupMenu";
import userEvent from "@testing-library/user-event";

describe("BasePopupMenu", () => {
  const mockOnClose = jest.fn();
  beforeEach(() => {
    mockOnClose.mockClear();
  });
  it("isVisible:false レンダリングされないこと", () => {
    const { queryByTestId } = render(
      <BasePopupMenu className="top-0" isVisible={false} onClose={mockOnClose}>
        <div>Content</div>
      </BasePopupMenu>
    );
    expect(queryByTestId("popupMenu")).toBeNull();
  });
  it("isVisible:true レンダリングされること", () => {
    const { getByTestId } = render(
      <BasePopupMenu className="top-0" isVisible={true} onClose={mockOnClose}>
        <div>Content</div>
      </BasePopupMenu>
    );
    expect(getByTestId("popupMenu")).toBeInTheDocument();
  });
  it("領域外をクリックした際にonCloseが呼ばれること", async () => {
    render(
      <BasePopupMenu className="top-0" isVisible={true} onClose={mockOnClose}>
        <div>Content</div>
      </BasePopupMenu>
    );
    await userEvent.click(document.body);
    expect(mockOnClose).toHaveBeenCalled();
  });
  it("領域内をクリックした際にonCloseが呼ばれないこと", async () => {
    const { getByTestId } = render(
      <BasePopupMenu className="top-0" isVisible={true} onClose={mockOnClose}>
        <div>Content</div>
      </BasePopupMenu>
    );
    await userEvent.click(getByTestId("popupMenu"));
    expect(mockOnClose).not.toHaveBeenCalled();
  });
});
