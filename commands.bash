python -m uv run manage.py runserver
docker-compose up
ngrok http 7880
cloudflared tunnel --url http://localhost:8000