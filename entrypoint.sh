#!/bin/sh

# Verifica se as variáveis de banco estão definidas
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

echo "Aguardando PostgreSQL em $DB_HOST:$DB_PORT..."

# Loop para verificar se o banco está pronto
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "PostgreSQL iniciado com sucesso."

# Rodar migrações
echo "Aplicando migrações..."
python manage.py migrate

# Coletar estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar servidor
if [ "$DEBUG" = "True" ]; then
    echo "Iniciando servidor de desenvolvimento..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Iniciando Daphne (Produção ASGI)..."
    # IMPORTANTE: Usando Daphne na porta 8000
    exec daphne -b 0.0.0.0 -p 8000 fleetvision.asgi:application
fi
