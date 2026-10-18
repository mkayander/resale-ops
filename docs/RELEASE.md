# Публичный релиз

Исходники опубликованы в [mkayander/resale-ops](https://github.com/mkayander/resale-ops) под MIT. Регистрация в магазинах плагинов выполняется отдельно; принятие в магазин не заявляется.

## Offline quality gate и тест артефакта

Перед реальным выпуском workflow `Release` запускает `python scripts/ci_quality.py`: Ruff, unit + mock-интеграционные тесты с coverage, проверку ZIP через `git archive`, распаковку в чистую папку и повторный запуск тестов. Это не вызывает Google API. На PR работает тот же gate через job `offline-quality`, и он должен быть обязательным статусом в branch protection.

Google smoke запускается **только вручную** в отдельном workflow `Google sandbox smoke (optional)` с специально выданными read-only правами к тестовым папке/таблице; он никогда не является обязательным статусом для релиза. Неполадки Google могут выдавать `INCONCLUSIVE`, но не останавливают публикацию репозитория. GitHub Actions, PyPI и npm registry остаются обычными внешними зависимостями pipeline.

Перед каждым релизом проверьте отсутствие личных фото, контактов, точных адресов, сессий браузера и реальных черновиков. Не добавляйте рабочий каталог продажи в репозиторий. Проверьте состав отслеживаемых файлов: `.gitignore` не исключает уже отслеживаемые данные.

Версию в `package.json`, `plugin.json` и `.claude-plugin/plugin.json` обновляет [semantic-release](https://semantic-release.gitbook.io/) в workflow [Release](../.github/workflows/release.yml) после merge в `main`. Коммиты в `main` должны следовать [Conventional Commits](https://www.conventionalcommits.org/): `feat:` — minor, `fix:` — patch, `BREAKING CHANGE:` или `feat!:` / `fix!:` — major; `chore:`, `docs:`, `ci:` и прочие типы по умолчанию релиз не создают.

Перед релизом выполните проверки из [TESTING.md](TESTING.md). Результаты ручной приёмки фиксируйте отдельно от автоматических тестов; не объявляйте невыполненные проверки успешными. Для MCP действует [ограничение проверенной ревизии](RU-MARKETPLACE-MCP.md), пока не выполнены критерии возобновления.

После успешного semantic-release появляются тег `vX.Y.Z`, GitHub Release с заметками и ZIP `resale-ops-X.Y.Z.zip` из `git archive`. Локальная проверка без публикации:

```sh
corepack enable
pnpm install --frozen-lockfile
pnpm exec semantic-release --dry-run
```

Ручной архив при необходимости:

```sh
git archive --format=zip --prefix=resale-ops/ --output=../resale-ops-0.4.0.zip HEAD
```

Проверьте распакованный архив теми же тестами. В нём не должно быть `.git`, виртуальных окружений и кэшей. Не заявляйте совместимость клиента как проверенную до его испытания.

Публичный репозиторий уже доступен для установки через skills.sh CLI. Для marketplace Claude Code и каталогов OpenAI/Cursor следуйте актуальным процедурам из [COMPATIBILITY.md](COMPATIBILITY.md). Скрипты этого проекта не регистрируют каталоги, не отправляют заявки и не выполняют push.
