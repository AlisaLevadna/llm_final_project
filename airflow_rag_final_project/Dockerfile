FROM apache/airflow:2.7.2-python3.11
ADD ./requirements/requirements.txt ./airflow_rag_final_project/requirements/
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r ./airflow_rag_final_project/requirements/requirements.txt