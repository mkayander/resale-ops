# Статус ru-marketplace-mcp

**С версии 0.4.0 готовое подключение удалено.** В рамках resale-ops сервер не запускается и его инструменты не вызываются. Интеграция сохранена как документация для проверки исходников и будущего разрешённого адаптера.

Профиль из 0.3.1 с названием «inspection» всё ещё предоставлял живые инструменты. `MARKETPLACE_SOURCES` ограничивает коннекторы, а не доступные операции. Проза skill не является техническим запретом вызовов, поэтому устанавливать такой профиль рядом с аккаунтом не рекомендуется.

Если вы ранее добавили `resale-market-research` или `resale-market-inspection`, отключите соответствующую запись в клиенте и обновите установленный skill. Обновление GitHub-репозитория не меняет клиентские настройки и личную копию skill. Этот проект не удаляет чужие подключения автоматически.

## Результат проверки исходников

Просмотренная ревизия: `cc89f2d87f59b8e2f2858db30a63208d439a7c3f`, 2026-10-15.

- В Яндекс-коннекторе непустой ответ HTTP 401/403 может попасть в обработку и кэш без передачи статуса агенту. HTTP 302 входит в повторы без классификации redirect.
- Avito/WB содержат имперсонацию и переходы транспорта, несовместимые с выбранным протоколом остановки.
- Источники ограничиваются переменной окружения, но доступ к live-инструментам этим не блокируется.
- Исправление этих дефектов не означает разрешения площадки на автоматизированный сбор.

Установка сервера, MCP-handshake и живые запросы не выполнялись. Это статическая проверка конкретной ревизии, не утверждение о каждой будущей версии.

## Что нужно для возвращения интеграции

Первичные условия площадки должны разрешать нужный способ и операцию для конкретного аккаунта. Затем проверяются транспорт, техническое ограничение инструментов/источников, обработка отказов, происхождение цены и соответствие SKU. Подробные критерии — в [адаптере skill](../skills/resale-ops/references/ru-marketplace-mcp.md). Проверки выполняются на фикстурах/официальной тестовой среде; аккаунт владельца не используется для исследования лимитов и антибота.

Для цены и объявления сейчас используйте [ручной режим](../skills/resale-ops/references/account-safety.md). Он не требует MCP и авторизации агента в аккаунте.

## Первичные исходники просмотренной ревизии

- [Выбор источников](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/mcp-core/src/mcp_core/source_selection.py).
- [Сравнение и проверка карточек](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/compare-connector/src/compare_connector/server.py).
- [Яндекс Маркет](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/yandex-connector/src/yandex_connector/server.py), [HTTP-транспорт](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/mcp-core/src/mcp_core/transport/http_tier.py).
- [Avito](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/avito-connector/src/avito_connector/server.py), [WB](https://github.com/Vladimir-Human/ru-marketplace-mcp/blob/cc89f2d87f59b8e2f2858db30a63208d439a7c3f/packages/wb-connector/src/wb_connector/server.py).
