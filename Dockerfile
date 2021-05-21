FROM python
COPY . /home
WORKDIR /home
RUN python3 -m pip install -r requirements.txt
CMD python3 src/integration_test.py
