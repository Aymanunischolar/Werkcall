const tsPlugin = require("@typescript-eslint/eslint-plugin");
const tsParser = require("@typescript-eslint/parser");
const n8nNodesBase = require("eslint-plugin-n8n-nodes-base");

module.exports = [
  {
    files: ["**/*.ts"],
    ignores: ["dist/**", "node_modules/**"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: "./tsconfig.json",
        sourceType: "module",
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      "n8n-nodes-base": n8nNodesBase,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      ...n8nNodesBase.configs.community.rules,
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "error",
    },
  },
];
