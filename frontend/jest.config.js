const nextJest = require("next/jest"); // eslint-disable-line @typescript-eslint/no-var-requires

const createJestConfig = nextJest({});

/** @type {import('@jest/types').Config.InitialOptions} */
const customJestConfig = {
  collectCoverage: true,
  collectCoverageFrom: [
    "<rootDir>/src/**/*.(ts|tsx)",
    "!<rootDir>/src/**/*.test.(ts|tsx)",
  ],
  coverageThreshold: {
    // TBD
    global: {
      // branches: 50,
      // functions: 60,
      // lines: 70,
      // statements: 70,
    },
  },
  // coverageProvider: "v8",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  setupFilesAfterEnv: ["./jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  testPathIgnorePatterns: [
    "<rootDir>/src/__tests__/__utils__",
    "<rootDir>/node_modules",
  ],
  transform: {
    "^.+\\.(t|j)sx?$": ["@swc/jest"],
  },
  extensionsToTreatAsEsm: [".ts", ".tsx"],
  transformIgnorePatterns: ["/node_modules/(?!next-auth|@auth/core|@panva/hkdf|jose)"],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
const jestConfig = async () => {
  const nextJestConfig = await createJestConfig(customJestConfig)();
  return {
    ...nextJestConfig,
    moduleNameMapper: {
      ...nextJestConfig.moduleNameMapper,
      "^next-auth/react$": "<rootDir>/__mock__/nextAuthReactMock.ts",
      "^next-auth$": "<rootDir>/__mock__/nextAuthMock.ts",
      "^next-auth/providers/(.*)$": "<rootDir>/__mock__/emptyMock.ts",
      "react-markdown": "<rootDir>/__mock__/emptyMock.ts",
      "rehype-rewrite": "<rootDir>/__mock__/emptyMock.ts",
      mermaid: "<rootDir>/__mock__/emptyMock.ts",
      "react-dnd": "react-dnd-cjs",
      "react-dnd-html5-backend": "react-dnd-html5-backend-cjs",
    },
  };
};

module.exports = jestConfig;
