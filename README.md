# llm_final_project

Steps to set up:

1. Create a project in Google Console, enable Google Drive API
2. Create a Service Account https://console.developers.google.com/iam-admin/serviceaccounts, download the json with the key
3. Share Google Drive folder with the Service Account
4. Put the json file into llm_final_project/airflow_rag_final_project/dags/refresh_dag/tokens/
5. Run the command to start redis: docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
6. cd to airflow_rag_final_project and run docker compose build, then docker compose up
7. Go to http://localhost:8080, log in with airflow/airflow
8. Add following variables to Admin -> Variables: open_ai_secret_key, service_account_token (the name of the file), redis_host (when running locally in docker will be host.docker.internal), folder_id (of the Google Drive folder)
9. Run the refresh_redis_vector_store DAG
10. Create .env file in flaskapp folder, put following variables:
    REDIS_URL=
    OPENAI_API_KEY=
12. cd to flask_app and rundocker build -t flask_app . , then docker run -p 9090:9090 flask_app
13. Send a Post request to http://localhost:9090/query with the body: { "question": "Your question to LLM?"}
