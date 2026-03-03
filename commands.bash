python -m uv run manage.py runserver 0.0.0.0:8000
python -m uv run manage.py migrate
ngrok http 8000