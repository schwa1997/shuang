FROM python:3.11

WORKDIR /app

COPY . /app
RUN pip install fastapi uvicorn prisma python-jose[cryptography] passlib[bcrypt] python-dotenv
RUN pip install --no-cache-dir -r requirements.txt
RUN prisma generate

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
