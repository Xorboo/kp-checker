FROM python:3

WORKDIR /usr/src/kp_checker

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY kp_checker.py ./

CMD [ "python", "./kp_checker.py" ]
