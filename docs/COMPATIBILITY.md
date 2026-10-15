# Форматы и каталоги

Проверено по первичным источникам 2026-10-15. Клиентские возможности меняются; ниже — основание упаковки, а не сертификат совместимости.

## Agent Skills

Стандарт задаёт папку с `SKILL.md`, обязательными `name`/`description` в YAML и Markdown-инструкциями. Пакет использует общие поля, относительные ссылки и supporting references; без клиентских `allowed-tools` или настроек разрешений. [Спецификация](https://agentskills.io/specification).

## Agent Plugins и приложения

Существует отдельный открытый [Agent Plugins](https://agent-plugins.org/) для упаковки skills и MCP. В проекте — корневой манифест стандарта 1.0.0 и папка `skills/`. MCP не включён автоматически.

OpenAI документирует этот формат для ChatGPT/Codex и отдельный публичный каталог плагинов; локальная установка и публичная подача — разные процессы. [Упаковка](https://developers.openai.com/plugins/build/plugins). Путь локального skill Codex: `.agents/skills` / `~/.agents/skills`. [Build skills](https://learn.chatgpt.com/docs/build-skills).

Cursor поддерживает Agent Plugins и собственные плагины; официальный marketplace требует рассмотрения, team marketplace — отдельная возможность. [Plugins](https://cursor.com/docs/plugins). Для простого копирования используйте `.cursor/skills` / `~/.cursor/skills`. [Skills](https://cursor.com/docs/skills).

Claude Code поддерживает `.claude/skills` / `~/.claude/skills`, а плагины используют собственный манифест. [Skills](https://code.claude.com/docs/en/skills). В проект добавлена такая оболочка; она использует ту же папку skills. Каталоги Claude Code распространяют плагины через marketplace. [Создание marketplace](https://code.claude.com/docs/en/plugin-marketplaces).

## Общая дистрибуция

[skills.sh](https://skills.sh/) — каталог экосистемы с установкой skills из репозиториев; [CLI Vercel](https://github.com/vercel-labs/skills) обслуживает несколько агентов. Это не единый официальный магазин всех клиентов и не гарантия проверки безопасности. GitHub ZIP/клонирование и копирование папки остаются независимым способом установки.

Регистрация в каталоге, наличие публичного репозитория и работоспособность формы Авито — три разные проверки. Ни одна публичная регистрация для этого проекта ещё не выполнена.
