import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

// ============================================================================
// ESLINT CONFIG - Optimized for Zero Bottleneck Development
// ============================================================================

export default tseslint.config(
  { ignores: ["dist", "node_modules", "build"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      // React Hooks rules
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      
      // TypeScript rules - relaxed for performance
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-require-imports": "off",
      "@typescript-eslint/no-non-null-assertion": "off",
      
      // Performance-focused rules
      "react-hooks/exhaustive-deps": "warn",
      "prefer-const": "warn",
      "no-shadow-restricted-names": "warn",
      
      // Allow console in development
      "no-console": "off",
      
      // Relax other rules for faster development
      "no-empty": "off",
      "no-irregular-whitespace": "off",
    },
  },
);
