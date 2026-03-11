
SELECT 'CREATE DATABASE shortener_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'shortener_test')\gexec