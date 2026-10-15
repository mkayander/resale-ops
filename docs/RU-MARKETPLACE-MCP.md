# Статус интеграции ru-marketplace-mcp

**В версии 0.3.1 живое исследование через MCP приостановлено.** Просмотренная ревизия `cc89f2d87f59b8e2f2858db30a63208d439a7c3f` допускается только для просмотра схем и `compare_sources`. Обычный сценарий через браузер работает независимо от интеграции. Основной пакет ничего не скачивает и не меняет настройки клиента.

Ревью выявило, что даже Яндекс-коннектор не полностью соблюдает требование остановки: `_fetch_html` не отклоняет непустые тела HTTP 401/403 и кэширует их; HTTP 302 входит в повторы без проверки назначения redirect. Возвращённые данные могут скрыть отказ от агента. Это уточняет прежнюю оценку в 0.3.0. Avito/WB также не допускаются из-за имперсонации и переключения транспорта. Юла не обнаружена в просмотренной ревизии.

Если вы подключили прежний профиль `resale-market-research`, отключите его в клиенте и обновите skill. Обновление файлов репозитория не меняет установленную копию skill или настройки приложения. Для обычного пользователя сервер сейчас не нужен.

## Для разработчика: инспекция без запросов к площадкам

Нужны Python 3.12+ и uv. Используйте отдельный checkout вне публичного проекта продажи. Если требуется проверить только регистрацию инструментов, после просмотра кода подготовьте окружение:

```sh
git clone https://github.com/Vladimir-Human/ru-marketplace-mcp.git
cd ru-marketplace-mcp
git checkout cc89f2d87f59b8e2f2858db30a63208d439a7c3f
uv sync --package compare-connector --frozen --no-dev
```

Не запускайте selfcheck/doctor: они обращаются к площадкам. Подготовка устанавливает зависимости; профиль источника ограничивает маршрутизацию запросов, но не является песочницей процесса. При обновлении повторяется проверка транспорта и схем.

## Настроить клиент

В [примере для инспекции](../examples/ru-marketplace-mcp.inspection.client.json) — формат mcpServers для Claude Code/Cursor. Он не устанавливается автоматически. Замените абсолютный путь и добавьте запись к существующим настройкам только для разработки. Для Codex используйте интерфейс настройки MCP с теми же command, args и env; JSON не является TOML-конфигом Codex. `--no-sync` не меняет подготовленное окружение при запуске; после обновления checkout окружение нужно синхронизировать явно.

`MARKETPLACE_SOURCES` оставьте равным `yandex_market`: пустое значение означает все источники. Сервер технически по-прежнему предоставляет инструменты живых запросов. Если клиент умеет ограничивать доступные инструменты, оставьте только `compare_sources`; иначе выполняйте инспекцию вручную, без автономного задания агенту. Не включайте Chrome/CDP или платные источники.

После подключения разрешён только `compare_sources` и просмотр схем. В `installed` и `searchable` ожидается только `yandex_market`; иной результат требует остановки и исправления настройки. Не делайте пробный запрос цены. Версия сервера из ответа не подтверждает точный Git commit: сверьте `git rev-parse HEAD` в checkout.

## Что нужно для возобновления

Исправленная закреплённая ревизия должна пройти проверки отказов 401/403/429, CAPTCHA и challenge redirects без повторов/кэширования/смены транспорта, а также выбор источника и соответствие SKU при проверке карточки. Полный порядок описан в [адаптере skill](../skills/resale-ops/references/ru-marketplace-mcp.md). Изменение переменных окружения или выбор другого источника не заменяет эту проверку. Автоматический патч стороннего кода в проект не добавлен.

## Пределы проверки

Транспорт и схемы просмотрены по исходникам. Сервер здесь не установлен; MCP-handshake, живые запросы и вход в аккаунт не выполнялись. End-to-end совместимость не заявляется. Профиль без CDP не требует доступа к личному Chrome.

Первичные источники закреплённой ревизии:

- [Выбор источников](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/mcp-core/src/mcp_core/source_selection.py).
- [Сравнение и проверка карточек](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/compare-connector/src/compare_connector/server.py).
- [Яндекс Маркет](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/yandex-connector/src/yandex_connector/server.py), [HTTP-транспорт](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/mcp-core/src/mcp_core/transport/http_tier.py).
- [Avito](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/avito-connector/src/avito_connector/server.py), [WB](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/wb-connector/src/wb_connector/server.py).
