import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SaveButton } from "./saveButton";

describe("SaveButton", () => {
  it("renders children correctly", () => {
    render(<SaveButton disabled={false}>Save</SaveButton>);
    expect(screen.getByText("Save")).toBeInTheDocument();
  });

  it("applies className correctly", () => {
    render(
      <SaveButton className="custom-class" disabled={false}>
        Save
      </SaveButton>
    );
    const button = screen.getByText("Save");
    expect(button).toHaveClass("custom-class");
  });

  it("applies id correctly", () => {
    render(
      <SaveButton id="save-button" disabled={false}>
        Save
      </SaveButton>
    );
    const button = screen.getByText("Save");
    expect(button).toHaveAttribute("id", "save-button");
  });

  it("handles onClick event", async () => {
    const handleClick = jest.fn();
    render(
      <SaveButton onClick={handleClick} disabled={false}>
        Save
      </SaveButton>
    );
    const button = screen.getByText("Save");
    await userEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when disabled prop is true", () => {
    render(<SaveButton disabled={true}>Save</SaveButton>);
    const button = screen.getByText("Save");
    expect(button).toBeDisabled();
  });

  it("is not disabled when disabled prop is false", () => {
    render(<SaveButton disabled={false}>Save</SaveButton>);
    const button = screen.getByText("Save");
    expect(button).not.toBeDisabled();
  });
});
