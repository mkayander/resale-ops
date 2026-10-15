/** @type {import('semantic-release').GlobalConfig} */
module.exports = {
  branches: ['main'],
  tagFormat: 'v${version}',
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    [
      'semantic-release-replace-plugin',
      {
        replacements: [
          {
            files: ['package.json'],
            from: '"version": "[0-9]+\\.[0-9]+\\.[0-9]+"',
            to: '"version": "${nextRelease.version}"',
          },
          {
            files: ['plugin.json'],
            from: '"version": "[0-9]+\\.[0-9]+\\.[0-9]+"',
            to: '"version": "${nextRelease.version}"',
          },
          {
            files: ['.claude-plugin/plugin.json'],
            from: '"version": "[0-9]+\\.[0-9]+\\.[0-9]+"',
            to: '"version": "${nextRelease.version}"',
          },
          {
            files: ['README.md'],
            from: 'Версия [0-9]+\\.[0-9]+\\.[0-9]+\\.',
            to: 'Версия ${nextRelease.version}.',
          },
        ],
      },
    ],
    [
      '@semantic-release/exec',
      {
        prepareCmd:
          'git archive --format=zip --prefix=resale-ops/ --output=resale-ops-${nextRelease.version}.zip HEAD',
      },
    ],
    [
      '@semantic-release/git',
      {
        assets: [
          'package.json',
          'pnpm-lock.yaml',
          'plugin.json',
          '.claude-plugin/plugin.json',
          'README.md',
        ],
        message:
          'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}',
      },
    ],
    [
      '@semantic-release/github',
      {
        assets: [
          {
            path: 'resale-ops-*.zip',
            label: 'resale-ops-${nextRelease.version}.zip',
          },
        ],
      },
    ],
  ],
};
