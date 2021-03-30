# This client was used for testing and troubleshooting connectivity to the DoTproxy server.
# It sends a static dns request asking for `google.com` and returns the raw byte response
# from the DoTproxy server.
import socket
import logging

logging.basicConfig(level=logging.INFO)

MAX_BYTE_SIZE = 512

# not a very accurate test case. Response quite dynamic, but should contain the keyword if successful
def test_when_google_dns_is_queried_then_the_response_should_contain_google(query=1):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        logging.debug(f'Conneting...')
        sock.connect(('127.0.0.1', 53))
        logging.debug(f'Query: {query} Connected...')

        udp_message = b'\xbd[\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
        sock.send(udp_message)

        response = sock.recv(MAX_BYTE_SIZE)
        logging.debug(f'Query {query} Server responded with: {response}')
        assert b'google' in response 