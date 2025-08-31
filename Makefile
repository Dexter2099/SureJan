.PHONY: bootstrap migrate seed recompute test astro

bootstrap:
	pip install -r requirements.txt

migrate:
	python manage.py makemigrations && python manage.py migrate

seed:
	python manage.py seed_demo

recompute:
        python manage.py recompute_ranks

test:
        pytest -q

astro:
	python manage.py compute_astro_baselines
