# llm_final_project

Steps to set up:

1. Create a project in Google Console, enable Google Drive API
2. Create a Service Account https://console.developers.google.com/iam-admin/serviceaccounts, download the json with the key
3. Share Google Drive folder with the Service Account
4. Put the json file into llm_final_project/airflow_rag_final_project/dags/refresh_dag/tokens/
5. Run the command to start redis: docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
6. (optional) if ollama needed run: docker run -d  -p 11434:11434 ollama/ollama:0.3.6   ; then pull needed models ; uncomment code for local models in both projects
8. cd to airflow_rag_final_project and run docker compose build, then docker compose up
9. Go to http://localhost:8080, log in with airflow/airflow
10. Add following variables to Admin -> Variables: open_ai_secret_key (if needed), embedding_base_url (if needed), service_account_token (the name of the file), redis_host (when running locally in docker will be host.docker.internal), folder_id (of the Google Drive folder)
11. Run the refresh_redis_vector_store DAG
12. Create .env file in flaskapp folder, put following variables:
    (if slack not needed - don't add and comment them out from other files)
    (choose open ai or local model or a xombination of both)
    REDIS_URL=
    OPENAI_API_KEY=
    EMBEDDING_MODEL_BASE_URL=
    MODEL_BASE_URL=
    SLACK_APP_TOKEN=
    SLACK_BOT_TOKEN=
13. cd to flask_app and rundocker build -t flask_app . , then docker run -p 9090:9090 flask_app

    if slack not needed - remove line: socket_mode_handler.start()
14. Send a Post request to http://localhost:9090/query with the body: { "question": "Your question to LLM?"}

15. if slack needed - install to workspace, add app to channel and text @ragbot search {your question}
