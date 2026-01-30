import eslintConfigPrettier from 'eslint-config-prettier';

export default [
  {
    ignores: ['node_modules/', 'dist/', 'services/', 'shared/', 'app-skeleton/'],
  },
  {
    files: ['**/*.js', '**/*.ts', '**/*.tsx'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-undef': 'off',
    },
  },
  eslintConfigPrettier,
];
