import os,sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

if __name__ == '__main__':
    from core import server_management
    while True:
        user_cmds = input('>>: ')
        cmds_parser = server_management.Management(user_cmds)