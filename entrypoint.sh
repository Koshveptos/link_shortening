


set -e

echo "🔄 Applying database migrations..."


until python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; asyncio.run(create_async_engine('${DATABASE_URL}').connect())" 2>/dev/null; do
    echo " Waiting for database..."
    sleep 2
done


alembic upgrade head

echo "Migrations applied. Starting application..."


exec uvicorn src.main:app --host 0.0.0.0 --port 8000
