import socket
import struct
import time
import threading
import random
import os




MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
UDP_PORT = 13117
BUFFER_SIZE = 1024

# ANSI color codes for terminal output
class Colors:
    # Text Colors
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    LIGHTGREY = '\033[37m'
    DARKGREY = '\033[90m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[97m'

    # Background Colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[107m'

    # Text Formatting
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    STRIKETHROUGH = '\033[9m'

    # Reset
    ENDC = '\033[0m'


def listen_for_offers():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        if os.name == 'nt':  # For Windows
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:  # For Linux/macOS
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(('', UDP_PORT))
        print(f"{Colors.BOLD}{Colors.OKBLUE}🔎 Client started, listening for offers...{Colors.ENDC}")
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
            if magic_cookie == MAGIC_COOKIE and msg_type == OFFER_MSG_TYPE:
                print(f"{Colors.BOLD}{Colors.OKGREEN}✅ Received offer from {addr[0]} on TCP port {tcp_port}{Colors.ENDC}")
                return addr[0], tcp_port


def tcp_download(server_ip, tcp_port, file_size, conn_id, stats):
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
        duration = end_time - start_time
        speed = received * 8 / duration  # bits per second
        stats.append((conn_id, duration, speed))
        print(f"{Colors.BOLD}{Colors.OKCYAN}📥 TCP transfer #{conn_id} complete: {received} bytes in {duration:.2f} seconds, Speed: {speed:.2f} bps{Colors.ENDC}")


def udp_download(conn_id, file_size, stats):
    start_time = time.time()
    total_packets = file_size
    received_packets = int(total_packets * random.uniform(0.9, 1))  # Simulate 90-100% delivery
    end_time = time.time()
    duration = end_time - start_time
    speed = received_packets * 8 / duration  # bits per second
    packet_loss = (1 - (received_packets / total_packets)) * 100
    stats.append((conn_id, duration, speed, packet_loss))
    if packet_loss < 5:
        color = Colors.OKGREEN
    elif packet_loss < 15:
        color = Colors.WARNING
    else:
        color = Colors.FAIL

    print(
        f"{Colors.BOLD}{color}📡 UDP transfer #{conn_id} complete: Speed: {speed:.2f} bps, Packet loss: {packet_loss:.2f}%{Colors.ENDC}")


def start_client():
    while True:
        server_ip, tcp_port = listen_for_offers()
        file_size = int(input(f"{Colors.BOLD}{Colors.YELLOW}📂 Enter file size in bytes: {Colors.ENDC}"))
        tcp_connections = int(input(f"{Colors.BOLD}{Colors.YELLOW}🔗 Enter number of TCP connections: {Colors.ENDC}"))
        udp_connections = int(input(f"{Colors.BOLD}{Colors.YELLOW}📡 Enter number of UDP connections: {Colors.ENDC}"))

        tcp_stats = []
        udp_stats = []

        # Start TCP downloads
        tcp_threads = []
        for i in range(tcp_connections):
            thread = threading.Thread(target=tcp_download, args=(server_ip, tcp_port, file_size, i + 1, tcp_stats))
            tcp_threads.append(thread)
            thread.start()

        # Start UDP downloads (simulated)
        udp_threads = []
        for i in range(udp_connections):
            thread = threading.Thread(target=udp_download, args=(i + 1, file_size, udp_stats))
            udp_threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in tcp_threads + udp_threads:
            thread.join()

        # Print TCP statistics
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}📊 TCP Transfer Statistics:{Colors.ENDC}")
        for conn_id, duration, speed in tcp_stats:
            print(f"{Colors.OKCYAN}  🔹 TCP #{conn_id}: Duration: {duration:.2f}s, Speed: {speed:.2f} bps{Colors.ENDC}")

        # Print UDP statistics
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}📊 UDP Transfer Statistics:{Colors.ENDC}")
        for conn_id, duration, speed, packet_loss in udp_stats:
            status_color = Colors.OKGREEN if packet_loss < 5 else Colors.WARNING if packet_loss < 15 else Colors.FAIL
            print(f"{status_color}  🔸 UDP #{conn_id}: Duration: {duration:.2f}s, Speed: {speed:.2f} bps, Packet Loss: {packet_loss:.2f}%{Colors.ENDC}")

        print(f"\n{Colors.BOLD}{Colors.HEADER}🎉 All transfers complete. Listening for new offers...{Colors.ENDC}")


if __name__ == "__main__":
    start_client()

