# Курсовая работа
# Система мониторинга и прогнозирования сбоев серверов

**Выполнила:** Симбирева Анастасия Андреевна  
**Группа:** 220032-11  
**Вариант:** 20

---

## Технологический стек

| Компонент | Технологии |
|---|---|
| Сбор метрик | Go 1.22 + gopsutil v3 + Prometheus client |
| Хранение метрик | Prometheus 2.52 |
| Анализ и прогнозирование | Python 3.11 + scikit-learn + NumPy |
| Визуализация | Grafana 10.4 |
| Уведомления | Telegram Bot API |
| API-слой ML-сервиса | FastAPI + uvicorn |
| Контейнеризация | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| SAST | gosec (Go) + bandit (Python) |

---

## Описание проекта

Распределённая система для **автоматического сбора метрик** серверов (CPU, RAM, диск), **детекции аномалий** двумя независимыми алгоритмами и **раннего оповещения** через Telegram.

Система решает три задачи:

1. **Непрерывный сбор** — Go-агент каждые 15 с опрашивает ОС через gopsutil и экспортирует метрики в формате Prometheus.
2. **Детекция аномалий** — ML-сервис каждые 60 с получает окно данных из Prometheus и прогоняет через два детектора:
   - **3σ (SigmaDetector)** — статистический, объяснимый, быстрый;
   - **Isolation Forest** — ML, улавливает нелинейные паттерны.
3. **Раннее предупреждение** — при обнаружении аномалии отправляется HTML-сообщение в Telegram с cooldown-защитой от дублей.

---

## Архитектура

```
┌──────────────┐   /metrics (Prometheus   ┌─────────────┐
│   Go-агент   │ ──────────────────────▶  │  Prometheus │
│  :9100       │   scrape each 15 s        │  :9090      │
└──────────────┘                           └──────┬──────┘
                                                  │ query_range API
                                           ┌──────▼──────┐
                                           │  ML-сервис  │
                                           │  :8000      │
                                           │  FastAPI    │
                                           │  3σ + IF    │
                                           └──────┬──────┘
                                                  │ Bot API
                                           ┌──────▼──────┐
                                           │   Telegram  │
                                           └─────────────┘
                                                  
┌──────────────┐
│   Grafana    │ ◀── Prometheus datasource
│  :3000       │
└──────────────┘
```

Поток данных:

1. Go-агент каждые **15 с** собирает CPU, RAM, диск и отдаёт `/metrics`.
2. Prometheus scrape-ит агента, хранит time-series.
3. ML-сервис каждые **60 с** запрашивает последний час данных через `query_range`.
4. Каждая метрика проходит через SigmaDetector и IsolationForestDetector.
5. При аномалии (и истёкшем cooldown) TelegramNotifier шлёт сообщение.
6. Grafana отображает метрики в реальном времени.

---

## Структура проекта

```
server-failure-prediction/
├── agent/                        # Go-агент сбора метрик
│   ├── cmd/agent/
│   │   ├── main.go               # точка входа, сборка зависимостей
│   │   ├── config.go             # loadConfig() из env-переменных
│   │   └── config_test.go
│   ├── internal/
│   │   ├── collector/
│   │   │   ├── collector.go      # интерфейс Collector
│   │   │   ├── metrics.go        # SystemMetrics struct
│   │   │   ├── system_collector.go  # gopsutil: CPU/RAM/диск
│   │   │   ├── gauges.go         # Prometheus Gauge × 3
│   │   │   ├── scraper.go        # polling loop
│   │   │   └── *_test.go
│   │   └── server/
│   │       ├── server.go         # HTTP /metrics + /healthz
│   │       └── server_test.go
│   ├── go.mod / go.sum
│   └── Dockerfile
│
├── ml_service/                   # Python ML-сервис
│   ├── app/
│   │   ├── main.py               # create_app(), lifespan
│   │   ├── settings.py           # pydantic-settings
│   │   ├── models.py             # MetricPoint, DetectionResult, DetectorKind
│   │   ├── worker.py             # AnalysisWorker (asyncio loop)
│   │   ├── alert_service.py      # cooldown + notifier
│   │   ├── api/
│   │   │   └── router.py         # POST /analyze, GET /healthz
│   │   ├── detector/
│   │   │   ├── base.py           # AnomalyDetector Protocol
│   │   │   ├── analysis_service.py
│   │   │   ├── sigma.py          # 3σ z-score
│   │   │   └── isolation_forest.py
│   │   ├── prometheus/
│   │   │   └── client.py         # PrometheusClient.fetch_range()
│   │   └── notifications/
│   │       ├── notifier.py       # TelegramNotifier
│   │       └── formatter.py      # format_alert() → HTML
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_sigma_detector.py
│   │   ├── test_isolation_forest_detector.py
│   │   ├── test_analysis_service.py
│   │   ├── test_alert_service.py
│   │   ├── test_worker.py
│   │   ├── test_prometheus_client.py
│   │   ├── test_router.py
│   │   ├── test_telegram.py
│   │   ├── test_settings.py
│   │   └── test_main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py                   # uvicorn entrypoint
│
├── infra/
│   ├── prometheus.yml            # scrape_configs: agent:9100
│   └── grafana/
│       ├── provisioning/
│       │   └── datasources/      # prometheus.yml datasource
│       └── dashboards/
│           └── server-agent.json # CPU / RAM / Disk panels + gauges
│
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

---

## Установка и запуск

### Требования

- Docker ≥ 24 и Docker Compose v2
- Go 1.22+ (только для локальной сборки агента)
- Python 3.11+ (только для локальной разработки ML-сервиса)

### Быстрый запуск через Docker Compose

```bash
# 1. Клонировать репозиторий
git clone https://github.com/hiitzn/server-failure-prediction.git
cd server-failure-prediction

# 2. Настроить переменные окружения
cp .env.example .env
# Открыть .env и указать TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID

# 3. Запустить все сервисы
docker-compose up --build
```

После запуска доступны:

| Сервис | URL |
|---|---|
| Go-агент (метрики) | http://localhost:9100/metrics |
| Go-агент (healthz) | http://localhost:9100/healthz |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin / admin) |
| ML-сервис (API) | http://localhost:8000/api/v1/healthz |
| ML-сервис (Swagger) | http://localhost:8000/docs |

### Локальный запуск (разработка)

**Go-агент:**
```bash
cd agent
go run ./cmd/agent
# Переопределение параметров через env:
LISTEN_ADDR=:9100 SCRAPE_INTERVAL=15s DISK_PATH=/ LOG_LEVEL=debug go run ./cmd/agent
```

**ML-сервис:**
```bash
cd ml_service
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Конфигурация

### Go-агент (переменные окружения)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `LISTEN_ADDR` | `:9100` | Адрес HTTP-сервера |
| `SCRAPE_INTERVAL` | `15s` | Интервал опроса ОС |
| `DISK_PATH` | `/` | Путь для мониторинга диска |
| `LOG_LEVEL` | `info` | Уровень логирования |

### ML-сервис (переменные окружения)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `PROMETHEUS_URL` | `http://prometheus:9090` | URL Prometheus |
| `LOOKBACK_SECONDS` | `3600` | Глубина окна анализа (сек) |
| `WORKER_INTERVAL_SECONDS` | `60` | Интервал фонового анализа (сек) |
| `MIN_DATA_POINTS` | `10` | Минимум точек для детекции |
| `SIGMA_THRESHOLD` | `3.0` | Порог z-score для 3σ |
| `IFOREST_CONTAMINATION` | `0.05` | Ожидаемая доля аномалий (IF) |
| `ALERT_COOLDOWN_MINUTES` | `15` | Cooldown между повторными алертами |
| `TELEGRAM_BOT_TOKEN` | — | Токен Telegram-бота |
| `TELEGRAM_CHAT_ID` | — | ID чата/канала |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

Если `TELEGRAM_BOT_TOKEN` или `TELEGRAM_CHAT_ID` не заданы, Telegram-уведомления отключаются автоматически — система продолжает работать, аномалии логируются.

---

## Тестирование

Все тесты запускаются одной командой:
```bash
make test
```

### Go-агент

```bash
cd agent
go test ./... -cover
```

| Пакет | Покрытие |
|---|---|
| `internal/server` | 100 % |
| `internal/collector` | 85.4 % |
| `cmd/agent` | 84.8 % |

Ключевые сценарии:
- Happy path + ошибки CPU/RAM/диска через инъекцию `osReader`
- Graceful shutdown HTTP-сервера через context cancellation
- Дубликаты регистрации Prometheus-метрик
- Скрапер: несколько тиков, ошибка коллектора не останавливает цикл

### ML-сервис

```bash
cd ml_service
pytest tests/ --cov=app --cov-report=term
```

Общее покрытие: **99 %**

| Модуль | Что тестируется |
|---|---|
| `sigma.py` | Стабильный ряд, спайк, нулевое std, нехватка данных |
| `isolation_forest.py` | Нормальный ряд, выброс, нехватка данных, невалидный contamination |
| `analysis_service.py` | Оркестрация: пустые данные, мок-детектор |
| `alert_service.py` | Cooldown, разные метрики, ошибка notifier |
| `worker.py` | CancelledError, исключения в цикле |
| `prometheus_client.py` | Парсинг, HTTP-ошибки, пустой результат |
| `router.py` | /healthz, /analyze, структура ответа |
| `telegram.py` | Успех, HTTP-ошибка, format_alert() |
| `settings.py` | Дефолты, кастомные значения |
| `main.py` | Lifespan, создание сервисов, Telegram enabled/disabled |

### SAST-анализ

```bash
make lint
# Go:     gosec ./agent/...
# Python: bandit -r ml_service/app/ -ll
```

Критических уязвимостей не обнаружено.

---

## API ML-сервиса

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/healthz` | Liveness probe |
| `POST` | `/api/v1/analyze` | Запуск полного цикла анализа |

Интерактивная документация (Swagger UI): http://localhost:8000/docs

### Пример: POST /api/v1/analyze

```bash
curl -X POST http://localhost:8000/api/v1/analyze | jq .
```

Ответ при обнаруженной аномалии:

```json
{
  "total": 6,
  "anomalies": 1,
  "results": [
    {
      "metric_name": "server_agent_cpu_usage_percent",
      "detector": "sigma",
      "is_anomaly": true,
      "score": 4.0982,
      "checked_at": "2026-06-07T17:54:44Z",
      "detail": "z=4.10, threshold=3.0, mean=15.39, std=2.40"
    },
    {
      "metric_name": "server_agent_cpu_usage_percent",
      "detector": "isolation_forest",
      "is_anomaly": false,
      "score": -0.1023,
      "checked_at": "2026-06-07T17:54:44Z",
      "detail": "if_score=-0.1023, contamination=0.05"
    }
  ]
}
```

### Telegram-уведомление

```
🔥 ANOMALY DETECTED

Metric:   server_agent_cpu_usage_percent
Detector: sigma
Score:    4.0982
Detail:   z=4.10, threshold=3.0, mean=15.39, std=2.40
Time:     2026-06-07 17:54:44 UTC
```

---

## Алгоритмы детекции

### 3σ (SigmaDetector)

Вычисляет z-score последней точки относительно всего окна:

```
z = |value_last - mean| / std
anomaly = z > threshold   (default threshold = 3.0)
```

**Плюсы:** объяснимый, не требует обучения, быстрый.  
**Минусы:** чувствителен к нестационарным рядам (суточные циклы CPU).

### Isolation Forest

Строит ансамбль случайных деревьев. Аномальные точки изолируются быстрее, поэтому получают отрицательный score (чем меньше — тем аномальнее).

Фичи: `[value, rolling_mean_5, rolling_std_5]` — временной контекст помогает отличить стабильно высокое значение от спайка.

**Плюсы:** нелинейные паттерны, не требует меток.  
**Минусы:** нужно ≥ 20 точек, менее объяснимый.

Оба детектора работают независимо на каждом цикле. Алерт отправляется, если хотя бы один из них сигнализирует об аномалии.

---

## Grafana Dashboard

Дашборд предустановлен через provisioning (не нужно ничего импортировать вручную).

Содержит:
- **3 time-series графика** — CPU, RAM, Disk с линией 2px и диапазоном 0–100 %
- **3 gauge-панели** — текущие значения с порогами: зелёный < 70 %, жёлтый 70–90 %, красный > 90 %
- Автообновление каждые **15 секунд**
- Временное окно по умолчанию — **последний час**

---

## Make-команды

```bash
make help          # справка
make deps          # go mod download + pip install
make test          # все тесты (Go + Python)
make test-agent    # только Go
make test-ml       # только Python
make coverage      # покрытие с отчётом
make lint          # gosec + bandit
make build         # сборка Go-бинаря
make docker-up     # docker-compose up -d --build
make docker-down   # docker-compose down
make run           # docker-compose up --build (с выводом)
make clean         # удалить артефакты сборки и кэши
```

---

## Выводы

В ходе выполнения курсовой работы:

1. Разработан **Go-агент** для сбора метрик CPU, RAM, диска с экспортом в формате Prometheus. Архитектура агента основана на инъекции зависимостей (`osReader`, `Collector` interface), что обеспечило 85 %+ тестовое покрытие без реального обращения к ОС.

2. Реализован **ML-сервис** на FastAPI с двумя алгоритмами детекции аномалий:
   - 3σ — статистический, быстрый, объяснимый;
   - Isolation Forest — ML, чувствительный к сложным паттернам временных рядов.

3. Настроена **полная наблюдаемость** через стек Prometheus + Grafana с предустановленным дашбордом.

4. Интегрированы **Telegram-уведомления** с cooldown-защитой от алертового шторма.

5. Достигнуто тестовое покрытие **>84 % для Go** и **99 % для Python**. Применены моки и Protocol-интерфейсы для изоляции компонентов.

6. Выполнены требования: контейнеризация Docker Compose, Git Flow, SAST-анализ (gosec + bandit), REST API с документацией Swagger.

Система готова к эксплуатации и расширяема: добавление новых метрик сводится к строке в `AGENT_METRICS`, нового детектора — к классу с методом `detect()`, нового канала уведомлений — к классу с методом `async send()`.