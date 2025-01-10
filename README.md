
# Network Speed Test - Client-Server Application

This project implements a client-server network speed test using Python. The server broadcasts offers via UDP and serves file downloads over both TCP and UDP. The client listens for offers and connects to the server to measure network speed.

## Features

- **Server**:
  - Broadcasts availability using UDP offer messages.
  - Handles TCP file transfers with multi-threading.
  
- **Client**:
  - Listens for server offers via UDP.
  - Initiates TCP download tests and measures transfer speed.

## File Structure

```
├── server.py  # Handles UDP offers and TCP file transfers
├── client.py  # Connects to the server and performs speed tests
└── README.md  # Project documentation
```

## Prerequisites

- Python 3.x
- Git (for version control)


## Running the Project

### 1. Start the Server
```bash
python server.py
```
The server will:
- Broadcast UDP offers every second.
- Listen for TCP connections on port `20000`.

### 2. Start the Client
```bash
python client.py
```
The client will:
- Listen for offers.
- Connect to the server and perform the speed test.

## Example Output

**Server Output:**
```
Server started, listening on TCP port 20000
```

**Client Output:**
```
Client started, listening for offers...
Received offer from 192.168.1.5 on TCP port 20000
Enter file size in bytes: 1000000
TCP transfer complete: 1000000 bytes in 2.34 seconds
```

## Contribution

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License.
