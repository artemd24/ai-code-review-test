# EPAM-test-task

## For running

1. First way for running solution, just run: `docker-compose up`

2. In case if it doesn't work you can follow next steps:
- Configure environment `python -m venv venv`
- Use environment `source venv/bin/activate`
- Install dependencies: `pip3 install -r requirements.txt`
- Create and insert envirnment values to .env file, about actual tokens you can ask me artemiidav@gmail.com
- Run MongoDB `docker-compose -d mongo`
- Run application `python3 app/__main__.py` или `python3 -m app` 
