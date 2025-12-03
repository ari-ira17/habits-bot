set -euo pipefail

REPO_DIR="/root/Projects/habits-bot"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
LOG_FILE="/tmp/deploy.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "=== Запуск процесса развертывания ==="

if ! cd "$REPO_DIR"; then
    log "Ошибка: Не удалось перейти в директорию $REPO_DIR"
    exit 1
fi

log "Выполнение git pull..."
GIT_OUTPUT=$(git pull origin main 2>&1 || true)
log "Git Output: $GIT_OUTPUT"

if echo "$GIT_OUTPUT" | grep -q "Already up to date."; then
    log "Код не изменился. Завершение работы."
    exit 0
fi

log "Обнаружены изменения. Переходим к пересборке и развертыванию."

log "Пересборка Docker образа 'bot'..."
docker compose $COMPOSE_FILES build bot >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    log "КРИТИЧЕСКАЯ ОШИБКА: Ошибка сборки образа."
    exit 1
fi

log "Обновление и перезапуск сервисов..."
docker compose $COMPOSE_FILES up -d --force-recreate bot >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    log "КРИТИЧЕСКАЯ ОШИБКА: Ошибка при запуске сервисов."
    exit 1
fi

log "Очистка неиспользуемых Docker ресурсов..."
docker system prune -f >> "$LOG_FILE" 2>&1 || true

log "=== Развертывание завершено успешно ==="
