
import socket
import struct
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
UDP_PORT = 13117
BUFFER_SIZE = 1024

def listen_for_offers():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', UDP_PORT))
        print("Client started, listening for offers...")
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
            if magic_cookie == MAGIC_COOKIE and msg_type == OFFER_MSG_TYPE:
                print(f"Received offer from {addr[0]} on TCP port {tcp_port}")
                return addr[0], tcp_port

def tcp_download(server_ip, tcp_port, file_size):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_ip, tcp_port))
        sock.sendall(f"{file_size}\n".encode())
        start_time = time.time()
        received = 0
        while True:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            received += len(data)
        end_time = time.time()
        print(f"TCP transfer complete: {received} bytes in {end_time - start_time:.2f} seconds")

def start_client():
    server_ip, tcp_port = listen_for_offers()
    file_size = int(input("Enter file size in bytes: "))
    tcp_download(server_ip, tcp_port, file_size)

if __name__ == "__main__":
    print("ohayo sekai good morning world")
    start_client()

