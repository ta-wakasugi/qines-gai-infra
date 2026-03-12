import "@testing-library/jest-dom";
import "whatwg-fetch";
import { TextDecoder, TextEncoder } from "util";

/**
 * This is a workaround to the problem of the jsdom library not supporting
 * URL.createObjectURL. See https://github.com/jsdom/jsdom/issues/1721.
 */
if (typeof window.URL.createObjectURL === "undefined") {
  window.URL.createObjectURL = jest.fn();
}

if (typeof global.TextEncoder === "undefined") {
  global.TextEncoder = TextEncoder;
}

if (typeof global.TextDecoder === "undefined") {
  global.TextDecoder = TextDecoder as unknown as typeof global.TextDecoder;
}

// This is a workaround to the problem of the jsdom library not supporting
// the `action` prop on the `form` tag. See
const IGNORE_ERROR_MESSAGE = [
  "Warning: Invalid value for prop %s on <%s> tag. Either remove it from the element, or pass a string or number value to keep it in the DOM. For details, see https://reactjs.org/link/attribute-behavior %s `action` form ",
  "Error: Not implemented: HTMLFormElement.prototype.requestSubmit",
];
const originalError = console.error;
console.error = (...args) => {
  const errorMessage = args.join(" ");
  if (IGNORE_ERROR_MESSAGE.some((message) => errorMessage.includes(message))) {
    return;
  }
  originalError(...args);
};
