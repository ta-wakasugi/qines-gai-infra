import { render, screen } from "@testing-library/react";
import Accordion from "./accordion";
import userEvent from "@testing-library/user-event";

describe("Accordion", () => {
  const title = "Test Accordion";
  const contentText = "Accordion Content";
  const content = <div>{contentText}</div>;

  it("レンダリング確認:アコーディオンのContentが非表示であること", () => {
    render(<Accordion title={title}>{content}</Accordion>);
    expect(screen.getByText(title)).toBeInTheDocument();
    expect(screen.queryByText(contentText)).not.toBeInTheDocument();
  });
  it("アコーディオンCloseでContentが非表示になること", async () => {
    render(<Accordion title={title}>{content}</Accordion>);
    const button = screen.getByText(title);
    await userEvent.click(button);

    expect(screen.getByText(contentText)).toBeInTheDocument();
    expect(screen.getByTestId("arrowUp")).toBeInTheDocument();

    await userEvent.click(button);
    expect(screen.queryByText(contentText)).not.toBeInTheDocument();
    expect(screen.getByTestId("arrowDown")).toBeInTheDocument();
  });
  it("アコーディオンOpenでContentが表示されること", async () => {
    render(<Accordion title={title}>{content}</Accordion>);
    const button = screen.getByText(title);
    await userEvent.click(button);
    expect(screen.getByText(contentText)).toBeInTheDocument();
    expect(screen.getByTestId("arrowUp")).toBeInTheDocument();
  });
});
