#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  echo "Usage: $0 {start|stop|restart|status}"
  exit 1
}

if ! command -v docker >/dev/null 2>&1; then
  echo "docker не найден"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "нужен Docker Compose V2: docker compose"
  exit 1
fi

cmd="${1:-}"

case "$cmd" in
  start)
    echo "Запуск контейнеров..."
    docker compose up -d --build
    echo
    docker compose ps
    echo
    echo "API: http://127.0.0.1:${APP_PORT:-8080}"
    echo "Swagger: http://127.0.0.1:${APP_PORT:-8080}/docs"
    ;;
  stop)
    echo "Остановка контейнеров..."
    docker compose down
    echo
    echo "Контейнеры остановлены"
    ;;
  restart)
    echo "Перезапуск контейнеров..."
    docker compose down
    docker compose up -d --build
    echo
    docker compose ps
    ;;
  status)
    docker compose ps
    ;;
  *)
    usage
    ;;
esac
