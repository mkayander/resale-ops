# Установка

## Надёжный путь: локальный skill

Скопируйте **всю папку** `skills/resale-ops`, включая `references`:

- Codex: `<ваш проект>/.agents/skills/resale-ops/` или `~/.agents/skills/resale-ops/`.
- Claude Code: `<ваш проект>/.claude/skills/resale-ops/` или `~/.claude/skills/resale-ops/`.
- Cursor: `<ваш проект>/.cursor/skills/resale-ops/` или `~/.cursor/skills/resale-ops/`.

`~` обозначает домашнюю папку пользователя. Не нужно устанавливать сразу в несколько каталогов одного приложения. Для начинающих предпочтительна установка только в отдельную папку проекта продажи.

Установщик, запущенный из корня скачанного проекта:

```sh
python scripts/install.py --agent codex --destination /path/to/sales-project
python scripts/install.py --agent claude --destination /path/to/sales-project
python scripts/install.py --agent cursor --destination /path/to/sales-project
```

В Windows замените путь на свой, например `"C:/Users/Anna/Documents/Sales"`. Для глобальной установки задайте домашнюю папку как `--destination`. Каталог назначения должен находиться вне исходного `skills/resale-ops`. Скрипт не скачивает зависимости, не меняет MCP и отказывается перезаписывать существующий skill. Символические ссылки и Windows junction в исходных файлах и пути установки отклоняются: выберите прямой путь к каталогу. При ошибке копирования неполный skill не появляется; повторите установку после устранения причины.

Обновление: сохраните свою старую копию **вне** каталогов обнаружения skills, затем удалите установленную папку вручную и повторите установку. Не оставляйте резервную копию рядом с активным skill: приложение может обнаружить оба. Лицензия включена в копируемую папку.

Откройте новую сессию. В Codex вызовите `$resale-ops`, в Claude Code и Cursor — `/resale-ops` или найдите его в меню skills. Если команда не обнаружена, попросите агента прочитать установленный `SKILL.md` и проверьте каталог.

## Плагин

Codex и Cursor: пакет с корневым `plugin.json` предназначен для клиентов с поддержкой Agent Plugins. Устанавливайте через доступный в вашей версии локальный источник/marketplace; если такого интерфейса нет, используйте установку skill выше. Доступность каталогов зависит от версии и аккаунта; репозиторий публичный, но пакет не опубликован в магазинах и не прошёл их проверку.

Claude Code: для временной локальной проверки из терминала:

```sh
claude --plugin-dir /absolute/path/to/resale-ops
```

В сессии вызовите `/resale-ops:resale-ops`. Для постоянной установки из нашего GitHub-каталога сообщества:

```sh
claude plugin marketplace add mkayander/resale-ops
claude plugin install resale-ops@mkayander-plugins --scope project
```

Каталог определён в `.claude-plugin/marketplace.json`, его имя — `mkayander-plugins`.
Плагин ссылается на корень этого же репозитория. После перезапуска сессии вызовите
`/resale-ops:resale-ops`. Это собственный каталог Max Kayander, не официальный
каталог Anthropic. Команды меняют настройки только при вашем запуске.
Не устанавливайте одновременно этот плагин и отдельный skill в Claude Code.

Обновить каталог: `claude plugin marketplace update mkayander-plugins`.
Обновить установленный плагин: `claude plugin update resale-ops@mkayander-plugins --scope project`.

## Установка из GitHub

Общий [установщик экосистемы skills.sh](https://github.com/vercel-labs/skills) поддерживает GitHub-репозитории, включая `mkayander/resale-ops` и skill `resale-ops`. Его запуск выполняет сторонний код. Для более осторожной установки используйте просмотренную копию репозитория и локальный установщик выше; он работает без сети и сторонних зависимостей.

Установка из папки проекта (нужен Node.js с `npx`):

```sh
npx skills add mkayander/resale-ops --skill resale-ops
```

Для просмотра доступных skills без установки:

```sh
npx skills add mkayander/resale-ops --list
```

Обновление установленных skills: `npx skills update` (проверьте список затронутых skills).
При необходимости отдельно закрепите версию CLI, затем проверьте предложенные агент и область установки. Не используйте безусловное согласие на все разрешения. Для воспроизводимости самого skill используйте проверенный commit или сохранённый ZIP, а не изменяемую ветку. Простая установка skill не должна требовать доступа к аккаунту маркетплейса.

Режим 0.5.0 — подготовка материалов для ручного размещения, без входа агента в аккаунт маркетплейса. Для телефон → ПК используйте [очередь в любом облаке](DRIVE-SHEETS-QUEUE.md) и `scripts/resale_queue.py` (сжатие и очистка EXIF в `photos/post/`). Поиск в интернете допустим; браузерный MCP и [ru-marketplace-mcp](RU-MARKETPLACE-MCP.md) не подключаются: если вы добавляли прежний профиль, отключите его вручную и обновите установленный skill.
