import pytest
from dot_proxy import * # on my machine the test gets stuck for more than about 280 threads # on my machine the test gets stuck for more than about 280 threads

UDP_MESSAGE = b'\xbd[\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01' 
TCP_MESSAGE = b'\x00\x1c\xbd[\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'

def test_when_requesting_dns_for_google_dot_com_then_tcp_message_should_prefix_2_bytes_with_length_of_udp_message_in_hex():
    udp_message = UDP_MESSAGE
    tcp_message = convert_udp_to_tcp(udp_message)
    assert tcp_message == TCP_MESSAGE

def test_when_converting_from_udp_to_tcp_message_then_tcp_should_be_2_bytes_longer():
    udp_message = UDP_MESSAGE
    tcp_message = convert_udp_to_tcp(udp_message)
    assert len(tcp_message) - len(udp_message) == 2

def test_when_converting_from_udp_to_tcp_should_be_of_type_byte():
    udp_message = UDP_MESSAGE
    tcp_message = convert_udp_to_tcp(udp_message)
    assert type(tcp_message) == bytes
    
def test_when_converting_a_udp_message_with_a_length_of_16_to_the_power_of_4_then_the_conversion_should_prefix_0xFFFF_in_escape_characters_for_hex():
    udp_message = b'w' * (65536 - 1)
    tcp_message = convert_udp_to_tcp(udp_message)
    assert tcp_message == b'\xff\xff' + udp_message
    
def test_when_tcp_message_converts_to_udp_message_then_the_prefixed_message_length_bytes_should_be_removed():
    tcp_message = TCP_MESSAGE
    udp_message = convert_tcp_to_udp(tcp_message)
    assert udp_message == tcp_message[2:]