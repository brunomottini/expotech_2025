FROM python:3.10

# Instalar dependencias necesarias para tu proyecto
RUN apt-get update && \
    apt-get install -y unixodbc freetds-bin

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
    apt-transport-https \
    curl \
    gnupg \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install --yes --no-install-recommends msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

WORKDIR /app

# Copiar todos los archivos del proyecto al contenedor
COPY ./ /app

# Copiar el archivo .env al contenedor
COPY .env /app/.env

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# Comando de inicio
CMD ["python", "app.py"]

