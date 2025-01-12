import socket
import struct
import time
import threading
import random
import os

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
REQUEST_MSG_TYPE = 0x3
PAYLOAD_MSG_TYPE = 0x4
UDP_PORT = 13117
BUFFER_SIZE = 4 * 1024


# Enhanced ANSI color codes for terminal output
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


# Listen for server offers via UDP
def listen_for_offers():
    """
    Listens for broadcast UDP offers from servers and returns the first valid offer's details.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        if os.name == 'nt':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(('', UDP_PORT))
        print(f"{Colors.BOLD}{Colors.OKBLUE}🔎 Client started, listening for offers...{Colors.ENDC}")
        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if len(data) >= 9:  # Ensure packet has enough data
                    magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
                    if magic_cookie == MAGIC_COOKIE and msg_type == OFFER_MSG_TYPE:
                        print(
                            f"{Colors.BOLD}{Colors.OKGREEN}✅ Received offer from {addr[0]} on TCP port {tcp_port}{Colors.ENDC}")
                        return addr[0], udp_port, tcp_port
            except struct.error:
                print(f"{Colors.BOLD}{Colors.FAIL}❌ Invalid packet received, ignoring...{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.BOLD}{Colors.FAIL}❌ Error while listening for offers: {e}{Colors.ENDC}")


# Perform TCP download
def tcp_download(server_ip, tcp_port, file_size, conn_id, stats):
    """
    Performs a file download over TCP and records the transfer statistics.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
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
            speed = received * 8 / duration if duration > 0 else 0
            stats.append((conn_id, duration, speed))
            # Removed duplicate print statement here
        except socket.error as e:
            print(f"{Colors.BOLD}{Colors.FAIL}❌ TCP connection error: {e}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.BOLD}{Colors.FAIL}❌ Error during TCP download: {e}{Colors.ENDC}")


# Perform UDP download
def udp_download(server_ip, udp_port, conn_id, stats, file_size):
    """
    Performs a file download over UDP and records the transfer statistics, including packet loss.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.settimeout(1)

        # Bind to all interfaces and an ephemeral port
        udp_sock.bind(('', 0))

        try:
            request_packet = struct.pack('!IbQ', MAGIC_COOKIE, REQUEST_MSG_TYPE, file_size)
            udp_sock.sendto(request_packet, (server_ip, udp_port))
            print(f"{Colors.BOLD}{Colors.OKBLUE}📨 Sent UDP request to {server_ip}:{udp_port}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.BOLD}{Colors.FAIL}❌ Error sending UDP request: {e}{Colors.ENDC}")

        try:
            start_time = time.time()
            received_packets = set()
            total_packets = 0
            packet_count = 0

            while True:
                try:
                    data, addr = udp_sock.recvfrom(BUFFER_SIZE)
                    if len(data) >= 21:
                        magic_cookie, msg_type, total_segments, current_segment = struct.unpack('!IbQQ', data[:21])
                        if magic_cookie == MAGIC_COOKIE and msg_type == PAYLOAD_MSG_TYPE:
                            received_packets.add(current_segment)
                            total_packets = total_segments
                            packet_count += 1

                            # Log every 100 packets received
                            if packet_count % 1000 == 0:
                                print(f"📡 Received UDP packet: Segment {current_segment + 1}/{total_segments}")

                            if current_segment + 1 == total_segments:
                                break
                        else:
                            print(f"📡 Received Unknown UDP packet {msg_type}")
                except socket.timeout:
                    print(f"📡 Received UDP timeout")
                    break  # End download after 1 second of inactivity

            end_time = time.time()
            duration = end_time - start_time
            packets_received = len(received_packets)
            packet_loss = ((total_packets - packets_received) / total_packets) * 100 if total_packets > 0 else 100
            speed = packets_received * BUFFER_SIZE * 8 / duration if duration > 0 else 0
            stats.append((conn_id, duration, speed, 100 - packet_loss))
        except Exception as e:
            print(f"{Colors.BOLD}{Colors.FAIL}❌ Error during UDP download: {e}{Colors.ENDC}")


# Main client function
def start_client():
    """
    Starts the client, listens for offers, and manages file transfers over TCP and UDP.
    """
    try:
        while True:
            server_ip, udp_port, tcp_port = listen_for_offers()
            file_size = int(input(f"{Colors.BOLD}{Colors.YELLOW}📂 Enter file size in bytes: {Colors.ENDC}"))
            tcp_connections = int(
                input(f"{Colors.BOLD}{Colors.YELLOW}🔗 Enter number of TCP connections: {Colors.ENDC}"))
            udp_connections = int(
                input(f"{Colors.BOLD}{Colors.YELLOW}📡 Enter number of UDP connections: {Colors.ENDC}"))

            tcp_stats, udp_stats, tcp_threads, udp_threads = [], [], [], []

            # Start TCP threads
            for i in range(tcp_connections):
                thread = threading.Thread(target=tcp_download, args=(server_ip, tcp_port, file_size, i + 1, tcp_stats))
                tcp_threads.append(thread)
                thread.start()

            # Start UDP threads and send requests
            for i in range(udp_connections):
                thread = threading.Thread(target=udp_download, args=(server_ip, udp_port, i + 1, udp_stats, file_size))
                udp_threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in tcp_threads + udp_threads:
                thread.join()

            # Print statistics
            for conn_id, duration, speed in tcp_stats:
                print(
                    f"{Colors.OKCYAN}📥 TCP transfer #{conn_id} finished, total time: {duration:.2f} seconds, speed: {speed:.2f} bps{Colors.ENDC}")

            for conn_id, duration, speed, success_rate in udp_stats:
                status_color = Colors.OKGREEN if success_rate >= 95 else Colors.WARNING if success_rate >= 85 else Colors.FAIL
                print(
                    f"{status_color}📡 UDP transfer #{conn_id} finished, total time: {duration:.2f} seconds, speed: {speed:.2f} bps, success rate: {success_rate:.2f}%{Colors.ENDC}")

            print(f"{Colors.BOLD}{Colors.HEADER}🎉 All transfers complete. Listening for new offers...{Colors.ENDC}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Colors.BOLD}{Colors.FAIL}❌ Client interrupted. Shutting down gracefully...{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.BOLD}{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")


if __name__ == "__main__":
    start_client()
