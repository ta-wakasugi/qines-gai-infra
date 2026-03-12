import { render, screen } from "@testing-library/react";
import BaseHeader from "./baseHeader";
import userEvent from "@testing-library/user-event";

describe("BaseHeader", () => {
  it("初期描画確認:パネルなし", () => {
    render(<BaseHeader />);
    expect(screen.getByTestId("logo")).toBeInTheDocument();
    expect(screen.queryByTestId("panelOnIcon")).toBeNull();
    expect(screen.queryByTestId("panelOffIcon")).toBeNull();
  });
  it("初期描画確認:パネルあり", () => {
    render(<BaseHeader isPanelDisplay />);
    expect(screen.queryByTestId("panelOnIcon")).toBeInTheDocument();
    expect(screen.queryByTestId("panelOffIcon")).toBeNull();
  });
  it("パネル押下時、アイコンが切り替わること", async () => {
    render(<BaseHeader isPanelDisplay />);
    await userEvent.click(screen.getByTestId("panelOnIcon"));
    expect(screen.queryByTestId("panelOnIcon")).toBeNull();
    expect(screen.queryByTestId("panelOffIcon")).toBeInTheDocument();
  });
  it("パネル2回押下時、アイコンが切り替わること", async () => {
    render(<BaseHeader isPanelDisplay />);
    await userEvent.click(screen.getByTestId("panelOffIcon"));
    expect(screen.queryByTestId("panelOnIcon")).toBeInTheDocument();
    expect(screen.queryByTestId("panelOffIcon")).toBeNull();
  });
});
