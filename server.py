
import socket
import threading
import struct
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
UDP_PORT = 13117
TCP_PORT = 20000
BUFFER_SIZE = 1024

def udp_broadcast():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        offer_msg = struct.pack('!IbHH', MAGIC_COOKIE, OFFER_MSG_TYPE, UDP_PORT, TCP_PORT)
        while True:
            sock.sendto(offer_msg, ('<broadcast>', UDP_PORT))
            time.sleep(1)

def handle_tcp_connection(conn, addr, file_size):
    data = b'1' * file_size
    conn.sendall(data)
    conn.close()

def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(('', TCP_PORT))
        server_sock.listen()
        print(f"Server started, listening on TCP port {TCP_PORT}")
        while True:
            conn, addr = server_sock.accept()
            file_size = int(conn.recv(BUFFER_SIZE).decode().strip())
            threading.Thread(target=handle_tcp_connection, args=(conn, addr, file_size)).start()

def start_server():
    threading.Thread(target=udp_broadcast).start()
    tcp_server()

if __name__ == "__main__":
    start_server()
