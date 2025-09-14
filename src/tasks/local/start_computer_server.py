# Synchronous usage
from computer_server import Server

server = Server(port=8000)
server.start()  # Blocks until stopped
