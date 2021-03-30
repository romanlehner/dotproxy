FROM python:3.9.1-alpine AS test
WORKDIR /dns-proxy
COPY requirements.txt . 
RUN pip3 install -r requirements.txt
COPY dot_proxy.py .
COPY unit_test.py .
RUN pytest --cov dot_proxy unit_test.py

FROM python:3.9.1-alpine
EXPOSE 53/udp
WORKDIR /dns_proxy
COPY --from=test /dns-proxy/dot_proxy.py .
CMD ["python", "dot_proxy.py"]
