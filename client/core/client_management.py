import socket, json, os
from core import client_main

print("welcome to Roger's FTP system".center(50, '-'))


class Management:
    """
    管理类，包括搭建连接，用户身份认证，以及其余client端的系统操作
    """
    header_size = 4
    recv_size_each = 1024
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    code = 'utf-8'
    saving_path = 'local'
    file_path = '%s/%s' % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), saving_path)

    def __init__(self):
        """
        一些数据属性的定义，连接建立，以及寻求客户输入
        """
        self.client = socket.socket(self.address_family, self.socket_type)
        self.server = input('Please enter the FTP server IP address: ')
        self.port = input('Please enter the FTP server port : ')
        while not self.connect_verify():
            self.__init__()

    def input_correction(self):
        """
        server和port的合法性验证
        :return: 若内容合法返回True，存在不合法返回False
        """
        if not self.server or not self.port:
            print('server与port不能为空')
            return False
        elif not self.port.isdigit():
            print('请输入正确的port！')
            return False
        else:
            return True

    def connect_verify(self):
        """
        确认通过输入的server，port是否连接成功
        :return:  失败返回False
        """
        if self.input_correction():
            try:
                self.client.connect((self.server, int(self.port)))
                data = self.client.recv(self.recv_size_each).decode(self.code)
                print(data)
            except:
                print('输入不符合规范，请重新输入！')
                return False
            self.login()
        else:
            return False

    def package(self, obj):
        """
        客户端发送信息打包成json并转换成二进制
        :param obj: 客户要发送的具体信息
        :return: 返回打包后的二进制信息
        """
        obj_json = json.dumps(obj)
        obj_bytes = obj_json.encode(self.code)
        return obj_bytes

    def login(self):
        """
        验证用户名与密码是否在对应库中，可错误输入三次
        :return:
        """
        count = 0
        while count != 3:
            user_name = input('请输入您的用户名：').strip()
            password = input('请输入您的密码：').strip()

            login_msg = {
                'func': 'login_verify',
                'user_name': user_name,
                'password': password
            }

            login_msg_bytes = self.package(login_msg)
            self.client.send(login_msg_bytes)

            msg = self.client.recv(self.recv_size_each).decode(self.code)
            judge, count = msg.split()
            count = int(count)
            if judge == 'True':
                main = client_main.Main(self)  # 客户端具体文件操作入口
            else:
                print('用户名或密码错误，请重试（还可尝试%s次）' % (3 - count))
        else:
            exit('您尝试登陆的次数过多，请联系管理员')
