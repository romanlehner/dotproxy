import socket
import ssl
import binascii
import logging
import threading

logging.basicConfig(level=logging.DEBUG)

PROXY_HOST = '0.0.0.0'
PROXY_PORT = 53 

# cloudflare-dns.com
DNS_SERVER_HOST= '1.1.1.1'
DNS_SERVER_PORT = 853
DNS_SERVER_HOST_NAME = 'cloudflare-dns.com'

MAX_BYTE_SIZE = 512 # UDP messages are restricted to 512 bytes according to https://tools.ietf.org/html/rfc1035#section-4.2.1

# DNS calls over TCP require to add a prefix of 2 bytes representing the length of the UDP request according to the RFC standard https://tools.ietf.org/html/rfc1035#section-4.2.2. 
def convert_udp_to_tcp(udp_message):
    length_udp = len(udp_message)
    tcp_prefix = binascii.unhexlify(hex(length_udp)[2:]) # we have to remove the first 2 digits of the hex string retured by hex() for unhexlify to work: e.g. 0x28 -> 28

    if length_udp < 256: # below 256 (decimal) binascii will only return a single byte representation. We have to add a zero on top: e.g. \x28 -> \x00\x28
        tcp_prefix = b'\x00' + tcp_prefix
    
    tcp_request = tcp_prefix + udp_message
    logging.debug(f'TCP prefix: {tcp_prefix} for UDP message length: {length_udp}')
    logging.debug(f'TCP message: {tcp_request}')
    return tcp_request

# Remove the first 2 bytes from the TCP message
def convert_tcp_to_udp(tcp_message):
    udp_message = tcp_message[2:]
    logging.debug(f'UDP message: {udp_message} for removed TCP prefix: {tcp_message[:2]}')
    return tcp_message[2:]

# Creates a new TCP socket and establishes a TLS encrypted connection
# Once the DNS query response is received the response will be returned in UDP format
# and the socket connection will be closed.
def get_dns(udp_sock, client_addr, udp_request):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
        tcp_sock.connect((DNS_SERVER_HOST, DNS_SERVER_PORT))

        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ssl_sock = context.wrap_socket(tcp_sock, server_hostname=DNS_SERVER_HOST_NAME)
        # Todo: Verify SSL certificate
        ssl_sock.sendall(convert_udp_to_tcp(udp_request))

        tcp_response = ssl_sock.recv(MAX_BYTE_SIZE)
        logging.info(f'Server {ssl_sock.getpeername()} Response: {tcp_response}')
        # Todo: Verify DNS query response

        udp_response = convert_tcp_to_udp(tcp_response)
        udp_sock.sendto(udp_response, client_addr)
        logging.info(f'Replied Client {client_addr} with {udp_response}')

# Waits for client to send DNS query and spins up a thread to serve the client so that the main process
# can take care of the next request.
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.bind((PROXY_HOST, PROXY_PORT))

        while True:
            logging.info('Wait for request...')
            udp_request, client_addr = udp_sock.recvfrom(MAX_BYTE_SIZE)

            logging.info(f'Serving Client: {client_addr}')
            logging.debug(f'Client: {client_addr} Requests: {udp_request}')
            query = threading.Thread(target=get_dns, args=(udp_sock, client_addr, udp_request))
            query.start()
            
if __name__ == "__main__":
    main()