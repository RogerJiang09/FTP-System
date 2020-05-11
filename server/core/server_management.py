import configparser, json, hashlib, socket, os, time
from conf import settings
from core import server_main


print("welcome to Roger's FTP system".center(50, '-'))


class Management:
    """
    管理类，包括搭建连接，用户身份认证，以及其余client端的系统操作
    有_前标的是内部代码，不标记是与用户的交互部分
    """

    def __init__(self, user_cmd):
        """
        判断用户输入，信息操作，错误返回上层
        :param user_cmd: 用户输入信息
        """
        self.verified_amount = 1
        if not self._input_verify(user_cmd):
            return

        self.cmd = user_cmd.lower()

        if not self._execute():
            return

    def _input_verify(self, user_cmd):
        """
        判断用户输入的合法性
        :param user_cmd: 用户输入信息
        :return: 合法返回True,否则返回False
        """
        if len(user_cmd.split()) != self.verified_amount:
            self._help()
            return False
        else:
            return True

    def _help(self):
        """
        帮助信息
        """
        msg = '''
        ***FTP系统操作以单个单词进行对应操作***
        创建客户账号：  create
        启动FTP系统：  start
        退出FTP系统：   exit
        '''
        print(msg)

    def _execute(self):
        """
        判断即执行客户输入，若输入错误打印帮助信息
        :return: 若错误返回False
        """
        if hasattr(self, self.cmd):
            getattr(self, self.cmd)()
        else:
            print('指令错误，请重新输入！')
            self._help()
            return False

    def _encryption(self, pss):
        """
        将明文的密码加密
        :param pss: 客户输入的密码
        :return: 加密后的密码
        """
        pss_md5 = hashlib.md5()
        pss_md5.update(pss.encode(settings.code))
        password = pss_md5.hexdigest()
        return password

    def _account_load(self):
        """
        用户传输信息可视化
        """
        self.config = configparser.ConfigParser()
        self.config.read_file(open(settings.accounts_dir))
        self.user_list = self.config.sections()

    def start(self):
        """
        start功能，建立端口等待连接，连接成功后发送成功提醒
        :return:
        """
        server_ftp = socket.socket(settings.address_family, settings.socket_type)
        server_ftp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_ftp.bind((settings.server, settings.port))
        server_ftp.listen(settings.max_listen)
        print('server: %s   port: %s 已启动' % (settings.server,settings.port))
        while True:
            print('等待信息。。。')
            self.conn, self.user_address = server_ftp.accept()
            self.conn.send('连接成功!'.encode(settings.code))
            print('%s接口已连入用户' % self.user_address[1])
            self._login_verify()

    def create(self):
        """
        创建新用户，并判断信息重复性，提供确认窗口，并在home目录下创建对应的文件夹
        :return:
        """
        self._account_load()
        user_name = input('请输入用户名：')
        if user_name in self.user_list:
            print('用户已经存在')
            return

        pss = input('请输入密码：')
        password = self._encryption(pss)
        capacity = str(int(input('用户可用容量（单位GB）：'))*(1024**3))  #转换GB为Bytes

        print('用户名：%s   密码：%s   容量：%s' % (user_name, pss, capacity))
        confirmation = input('以上信息是否正确，请输入Y或者N：')
        if confirmation.upper() == 'N':
            return

        self.config.add_section(user_name)
        self.config.set(user_name, 'password', password)
        self.config.set(user_name, 'capacity', capacity)
        self.config.set(user_name, 'usage', '0')
        self.config.write(open(settings.accounts_dir, 'r+'))
        os.mkdir('%s/%s' % (settings.home_dir, user_name))
        print('%s创建成功' % user_name)
        return

    def exit(self):
        exit('FTP系统已退出！')

    def _login_verify(self):
        """
        客户身份认证
        :return:
        """
        self._account_load()
        count = 0
        while count != 3:
            login_msg_recv = self.conn.recv(settings.recv_size_each)
            login_msg = json.loads(login_msg_recv)
            if login_msg['user_name'] in self.user_list:
                input_username = login_msg['user_name']
                input_pss = login_msg['password']
                input_password = self._encryption(input_pss)
                saving_password = self.config.get(input_username, 'password')
                if input_password != saving_password:
                    count += 1
                    self.conn.send(('False %s' % count).encode(settings.code))
                else:
                    self.conn.send('True 0'.encode(settings.code))
                    self.user_name = input_username
                    print('用户%s登陆成功' % input_username)
                    main = server_main.Main(self)  # 登陆成功，调用对象
                    return

            else:
                count += 1
                self.conn.send(('False %s' % count).encode(settings.code))
        else:
            return

