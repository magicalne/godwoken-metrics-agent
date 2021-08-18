FROM python:3.9
RUN pip install pipenv
ENV MONITOR_NODE_IP=godwoken.web3
# COPY Pipfile* /tmp
# RUN cd /tmp && pipenv lock --keep-outdated --requirements > requirements.txt
# RUN pip install -r /tmp/requirements.txt
COPY . /tmp/myapp
RUN cd /tmp/myapp && pipenv install
CMD cd /tmp/myapp && pipenv run python -m agent 3000