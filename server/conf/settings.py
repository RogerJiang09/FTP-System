import socket, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

header_size = 4

recv_size_each = 1024

address_family = socket.AF_INET

socket_type = socket.SOCK_STREAM

code = 'utf-8'

server = '127.0.0.1'

port = 9295

max_listen = 5

accounts_dir = '%s/conf/accounts.ini' % BASE_DIR

home_dir = '%s/home' % BASE_DIR