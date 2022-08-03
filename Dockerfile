FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1


#COPY ./pyproject.toml ./pyproject.toml
COPY ./requirements.txt .
COPY ./README.md .
COPY ./setup.py .
COPY ./enr_app enr_app
COPY ./data/app.gpkg data/
COPY ./data/epcis.csv data/
COPY ./data/indicateurs.csv data/

RUN pip install --upgrade pip setuptools wheel \
    && pip install -e . \
    && pip cache purge \
    && rm -rf /root/.cache/pip

ENV STREAMLIT_SERVER_PORT 3838
EXPOSE $STREAMLIT_SERVER_PORT
ENTRYPOINT ["streamlit", "run"]
CMD [ "enr_app/01_🏠_Accueil.py" ]
