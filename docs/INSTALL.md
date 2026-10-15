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

В Windows замените путь на свой, например `"C:/Users/Anna/Documents/Sales"`. Для глобальной установки задайте домашнюю папку как `--destination`. Скрипт не скачивает зависимости, не меняет MCP и отказывается перезаписывать существующий skill. Обновление: сначала сохраните свою старую копию отдельно, затем удалите её вручную и повторите установку.

Откройте новую сессию. В Codex вызовите `$resale-ops`, в Claude Code и Cursor — `/resale-ops` или найдите его в меню skills. Если команда не обнаружена, попросите агента прочитать установленный `SKILL.md` и проверьте каталог.

## Плагин

Codex и Cursor: пакет с корневым `plugin.json` предназначен для клиентов с поддержкой Agent Plugins. Устанавливайте через доступный в вашей версии локальный источник/marketplace; если такого интерфейса нет, используйте установку skill выше. Доступность каталогов зависит от версии и аккаунта; пакет ещё не опубликован и не прошёл проверку магазина.

Claude Code: для временной локальной проверки из терминала:

```sh
claude --plugin-dir /absolute/path/to/resale-ops
```

В сессии вызовите `/resale-ops:resale-ops`. Для постоянного распространения используйте marketplace Claude Code по официальной инструкции из `COMPATIBILITY.md`. Здесь marketplace намеренно не зарегистрирован и ничего не устанавливается в аккаунт автоматически.

## Установка из GitHub

Общий установщик экосистемы skills.sh поддерживает установку из GitHub:

```sh
npx skills add mkayander/resale-ops --skill resale-ops
```

Проверьте предложенные агент и область установки; не используйте безусловное согласие на все разрешения. Для воспроизводимости используйте проверенный tag/commit или ZIP релиза.

Дополнительное исследование цен: [ru-marketplace-mcp](RU-MARKETPLACE-MCP.md). Его подключение выполняется отдельно и не требуется для установки skill.
