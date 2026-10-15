# Подключение ru-marketplace-mcp

Интеграция опциональная: skill использует инструменты уже подключённого сервера. Основной пакет ничего не скачивает и не меняет настройки клиента. Черновики заполняются отдельным браузерным инструментом.

Первая интеграция ограничена Яндекс Маркетом как ориентиром цены нового товара. Б/у аналоги Авито проверяются обычным браузером. Транспорт Avito/WB upstream содержит имперсонацию и переключения, несовместимые с запретом обходов в resale-ops; эти источники исключены из примера. Юла не обнаружена в проверенной ревизии.

## Подготовить сервер

Нужны Python 3.12+ и uv. Используйте отдельный checkout вне публичного проекта продажи. Команды выполняются отдельно после просмотра кода:

```sh
git clone https://github.com/Vladimir-Human/ru-marketplace-mcp.git
cd ru-marketplace-mcp
git checkout cc89f2d87f59b8e2f2858db30a63208d439a7c3f
uv sync --all-packages --frozen
```

Просмотренная ревизия закреплена; работоспособность в вашей сети требует проверки. При обновлении повторяется проверка транспорта и схем.

## Настроить клиент

В `examples/ru-marketplace-mcp.client.json` — пример формата mcpServers для Claude Code/Cursor. Замените абсолютный путь и добавьте запись к существующим настройкам. Не заменяйте весь конфиг. Для Codex используйте интерфейс настройки MCP с теми же command, args и env; JSON не является TOML-конфигом Codex.

Пример не является автоматически подключаемым корневым `mcp.json`. `MARKETPLACE_SOURCES` оставьте равным `yandex_market`: пустое значение означает все источники. Для этого профиля не запускайте общий doctor, Chrome/CDP или платные источники.

После подключения проверьте `compare_sources`, текущие схемы и один запрос известной модели с явно заданным `sources=["yandex_market"]`. Проверьте прямую карточку, обычную цену, вариант, регион и предупреждения. Отдельно соберите сопоставимые б/у объявления: цена нового товара не входит в их медиану.

## Пределы проверки

Транспорт и схемы просмотрены по исходникам. Сервер здесь не установлен, живые запросы и вход в аккаунт не выполнялись; end-to-end совместимость не заявляется. Инструкции ограничения источников не являются технической песочницей стороннего процесса. Профиль без CDP не требует доступа к личному Chrome.

Первичные источники закреплённой ревизии:

- [Выбор источников](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/mcp-core/src/mcp_core/source_selection.py).
- [Сравнение и проверка карточек](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/compare-connector/src/compare_connector/server.py).
- [Яндекс Маркет](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/yandex-connector/src/yandex_connector/server.py), [HTTP-транспорт](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/mcp-core/src/mcp_core/transport/http_tier.py).
- [Avito](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/avito-connector/src/avito_connector/server.py), [WB](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/wb-connector/src/wb_connector/server.py).
