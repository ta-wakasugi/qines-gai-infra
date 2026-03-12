import React from "react";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CheckboxInput } from "./checkboxInput";

describe("CheckboxInput component", () => {
  it("checkedがtrueなら、チェックマークのsvgが表示される", () => {
    const { getByRole } = render(
      <CheckboxInput checked={true} label="test" onClick={() => {}} />
    );
    expect(getByRole("checkbox").querySelector("svg")).toBeInTheDocument();
  });

  it("checkedがfalseなら、チェックマークのsvgが表示されない", () => {
    const { getByRole } = render(
      <CheckboxInput checked={false} label="test" onClick={() => {}} />
    );
    expect(getByRole("checkbox").querySelector("svg")).not.toBeInTheDocument();
  });

  it("クリックされたらhandleClickが呼ばれる", async () => {
    const handleClick = jest.fn();
    const { getByRole } = render(
      <CheckboxInput checked={false} label="test" onClick={handleClick} />
    );
    await userEvent.click(getByRole("checkbox"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
