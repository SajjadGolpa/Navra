FROM python:3.9
WORKDIR /code
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 9000
COPY . .
CMD python Main.py