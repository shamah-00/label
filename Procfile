web: python manage.py collectstatic --noinput --settings=swiftcart.production_settings && gunicorn swiftcart.wsgi:application --bind 0.0.0.0:$PORT
