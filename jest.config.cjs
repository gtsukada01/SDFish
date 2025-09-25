module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/scripts/test'],
  testMatch: ['**/*.jest.test.js'],
  transform: {},
  moduleFileExtensions: ['js', 'cjs', 'mjs', 'json'],
  setupFilesAfterEnv: ['<rootDir>/scripts/test/jest.setup.js']
};
