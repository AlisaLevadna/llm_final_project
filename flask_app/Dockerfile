FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader punkt

EXPOSE 9090

# Run both Flask app and Slack bot
CMD ["sh", "-c", "python /app/answer_questions_app.py & python /app/slack_bot.py"]
