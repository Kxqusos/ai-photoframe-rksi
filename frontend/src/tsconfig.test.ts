import { readFileSync } from "node:fs";
import { resolve } from "node:path";

test("frontend declares a tsconfig that enables the automatic React JSX runtime", () => {
  const tsconfigPath = resolve(__dirname, "..", "tsconfig.json");
  const raw = readFileSync(tsconfigPath, "utf8");
  const tsconfig = JSON.parse(raw) as {
    compilerOptions?: {
      jsx?: string;
      types?: string[];
    };
  };

  expect(tsconfig.compilerOptions?.jsx).toBe("react-jsx");
  expect(tsconfig.compilerOptions?.types).toContain("vitest/globals");
  expect(tsconfig.compilerOptions?.types).toContain("vite/client");
});
