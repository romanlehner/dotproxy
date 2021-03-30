# DoTproxy (DNS over TLS)
DoTProxy is an experimental project that intends to encrypt DNS queries with TLS. It origniated from a challenge I got from a job interview and happend to be a great opportunity to get myself more involved in network and coding topics. 

# Run DoTproxy
## With Docker Compose
Use [docker-compose](docker-compose.yaml) to build and run the DoTproxy container in the background:

    docker-compose up -d

To check the status of the container or shut it down:

    docker-compose ps
    docker-compose down

> **NOTE:** I decided to run the unit tests as part of the [dockerbuild](dockerfile) to force myself to never build a container without tested code. This might not be the common practice but I found it useful for local development. When running the build with docker-compose you should see the test run output in the console.

## Test DoTproxy with dig or nslookup
Use `dig` or `nslookup` to test the DNS query by specifying the host and port of DoTproxy:

    nslookup google.com localhost -port 53
    dig google.com @localhost -p 53

## Run from Source (UNIX)
DoTproxy was developed using `Python 3.9.1`. Create a virtual environment and run the python script with sudo (port 53 requires root permission):

    pip install virtualenv
    virtualenv --python /usr/bin/python3.9.1 env
    source env/bin/activate
    sudo python dot_proxy.py

## Run Unit Tests
To run [unit tests](unit_test.py) with coverage install the required libraries and run pytest:

    pip install -r requirements.txt
    pytest --cov dot_proxy unit_test.py 

## Run E2E Tests
To run the [e2e test](e2e_client_test.py) first start DoTproxy then run with pytest:

    docker-compose up -d
    pytest e2e_client_test.py -o log_cli=true -o log_level=INFO
    docker-compose down

## Run Load Test
To run the [load test](load_test.py) first start DoTproxy then run with pytest. The container stats can be viewed with `docker stats`:

    docker-compose up -d
    docker stats dot-proxy
    pytest load_test.py -o log_cli=true -o log_level=INFO
    docker-compose down

> **NOTE:** As of the current version the load testing script can only perform up to 250 concurrent requests. Above the test will get stuck as the threads are not processes (cause yet to be explored).

# Design Choises
The first draft of DoTproxy waits for a UDP connection on `localhost:53` and forwards the DNS query to `Cloudflare DNS` on `1.1.1.1:853` by a TLS encrypted TCP connection. Every request creates a new TCP socket and closes it after the response has been received. 

> **Version v0.0.1:** The system in a blocking state being able to serve only a single request at a time. Based on the simplified [load test](#run-load-test) this version is able to handle 100 concurrent requests in about 8 seconds (12 queries per second). 

> **Version v0.0.2:** Spins up TCP sockes for each DNS query so that the main thread can process the next incoming request on the UDP socket on port 53. Implemented with python [threading library](https://docs.python.org/3/library/threading.html). Based on the simplified [load test](#run-load-test) this version is able to handle 100 concurrent requests in about 0.5 seconds (200 queries per second). 

More considerations and improvement points can be found in the [room for improvements](#room-for-improvements) section.

## Security Concerns
While DNS-over-TLS is encrypted, all DNS queries are performed exclusively over port 53 as per [RFC1035](https://tools.ietf.org/html/rfc1035#section-4.2.1). This allows attacks to specify a precise target where in contrast DNS-over-HTTPS is performed on port 443 which blends with other requests over the network and therefore might me more difficult to identify. 

Depending on the system architecture there might be other attack surfaces such as a cache or the still unprotected network connection between DNS requester and DoTproxy. This might be especially significant for attacks from within the system. 

## Integration to Distributed Systems
A production ready DoT proxy could be deployed in multiple ways. It could act as centralized DNS Gateway that any internal service can query. Assuming the number of queries is significantly high, DoTproxy would be required to be either performant enough and/or scalable. We would also have to think of availability and resilience of the system, as the proxy becomes a single point of failure. 

Going the opposite direction, we could think of utilizing a container side-car pattern by attaching DoTproxy to running containerized services, enforcing services to perform DNS queries over DoTproxy. In that case the load on a single instance might be significantly reduced in contrast to the centralized architecture and we eliminate a single point of failure. While the design complexity of DoTproxy might be reduced, we might experience an increase of operational overhead in terms of overall cpu, memory and disk resources required, as well as maintaining and updating the system.

## Room for Improvements
Here are some improvements I could think of based on the current design presented:
- SSL certificate verification
- DNS query and response verification
- Caching
- Health and Readiness probing
- Error Handling
- Allow to query multiple DNS server

### SSL certificate verification
While the current system is performing a TLS handshake and encrypts data with the provided certificate by the server, there should be a mechanism to verify the correctness and validity of the certificate. The server might deliver an expired or untrusted certificate. At this point I would want to make sure that the certificate doesn't come from an attacker who might either read the data or redirect to malicious IP addresses. 

### DNS response verification
The DNS query should be checked on correctness and formatting before the connection to the DNS server is established. Also the server response should be verified before returned to the requester. 

### Caching
A caching system allows to reduce unecessary network exposure as well as reducing query time. Caching might introduce new complexities such as expiry, concurrency or invalid DNS entries. 

### Health and Readiness probing
Currently DoTproxy dosn't have any specific ports for checking its functional state. While the single port 53 could be used, it would also block actual DNS requests from being processed. 

### Error Handling
As mentioned in previous sections the current version does not have any specific error handlings. If something fails the socket is supposed to close the connection and a new request has to be made by the client. There aren't any verification steps and routines when something goes wrong.

### Allow to query multiple DNS server
DoTproxy only queries cloudflare DNS on `1.1.1.1:853`. We could set an environment variable to query different DNS servers and modify the query to the requirements of the provider if necessary.

# Resources
- [SPKI Certificate Theory](https://tools.ietf.org/html/rfc2693)
- [Domain Name Specifications - UDP and TCP usage](https://tools.ietf.org/html/rfc1035#section-4.2.1)
- [Python Socket Library](https://docs.python.org/3/library/socket.html#socket.socket.accept)
- [Socket Programming in Python - Real Python](https://realpython.com/python-sockets/)
- [Socket Programming in Python - Educative.io](https://www.educative.io/courses/grokking-computer-networking/N73706w7Br6)
- [Python SSL Library](https://docs.python.org/3/library/ssl.html)
- [Cloudflare 1.1.1.1 - Documentation](https://developers.cloudflare.com/1.1.1.1/)
- [What is an on-path attacker - Cloudflare blog](https://www.cloudflare.com/en-gb/learning/security/threats/on-path-attack/)
- [Zero Trust Security - Cloudflare blog](https://www.cloudflare.com/en-gb/learning/security/glossary/what-is-zero-trust/)
- [DoT vs DoH - Cloudflare blog](https://www.cloudflare.com/en-gb/learning/dns/dns-over-tls/)
- [OpenSSl client for SSL testing](https://docs.pingidentity.com/bundle/solution-guides/page/iqs1569423823079.html)
- [TLS Handshake - Cloudflare blog](https://www.cloudflare.com/en-gb/learning/ssl/what-happens-in-a-tls-handshake/)
- [Hexadecimal definition - Wikipedia](https://simple.wikipedia.org/wiki/Hexadecimal#:~:text=The%20hexadecimal%20numeral%20system%2C%20often,numbers%20and%20six%20extra%20symbols.)
- [Concurrency in Python - Real Python](https://realpython.com/python-concurrency/)
- [Let localhost be localhost - RFC](https://tools.ietf.org/html/draft-ietf-dnsop-let-localhost-be-localhost-02)
