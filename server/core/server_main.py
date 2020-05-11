import hashlib, os, struct, json, shutil, time
from conf import settings


class Main:
    """
    数字对应列表（为了稳定某些功能的收取需求，保证收取的长度一致）：
    response_list = {
        '200': '文件存在，准备传输',
        '300': '文件夹为空',
        '999': '存在错误，文件不存在',
    }
    主体交互部分，客户端登陆后相关操作的对应，包括上传下载，用户下载断点重启自动续传，目录即文件的增删改查
    有_前标的是内部代码，不标记是与用户的交互部分
    """
    def __init__(self, obj):
        """
        传入，conn，调用accoutns.ini方式，以及循环判断客户端传来的用户输入的合法性并进行对应执行
        :param obj: management直接传入，作提取参数用
        """
        self.management_instance = obj  # management对象
        self.config = obj.config  # accounts.ini调用对象
        self.user_name = self.management_instance.user_name
        self.main_server = self.management_instance.conn  # 传输链接
        self.max_verified_amount = 2
        self.config[self.user_name]['user_home'] = '%s/%s' % (settings.home_dir, self.user_name)
        self.current_menu = [self.config[self.user_name]['user_home']]
        self.reconnection()

        while True:
            user_cmds = self.main_server.recv(settings.recv_size_each).decode(settings.code)
            if not user_cmds:
                print('用户断开连接！')
                self.main_server.close()
                break

            if not self._input_verify(user_cmds):
                self.main_server.send('Fail'.encode(settings.code))
                continue

            self.input_cmds = user_cmds.split()

            if not self._execute():
                self.main_server.send('Fail'.encode(settings.code))
                continue

    def _input_verify(self, user_cmd):
        """
        判断用户输入的合法性
        :param user_cmd: 用户输入信息
        :return: 合法返回True,否则返回False
        """
        if len(user_cmd.split()) > self.max_verified_amount:
            return False
        else:
            return True

    def _execute(self):
        """
        判断即执行客户输入，若输入错误打印帮助信息
        :return: 若错误返回False
        """
        if hasattr(self, self.input_cmds[0].lower()):
            self.main_server.send('receive'.encode(settings.code))
            getattr(self, self.input_cmds[0].lower())()
            return True
        else:
            print('指令错误')
            return False

    def _header_pack(self):
        """
        报头打包
        :return:  返回用json打包后的报头
        """
        self._file_encryption(self.file_path)
        header_dic = {
            'file_name': self.input_cmds[1],
            'md5': self.file_md5,
            'file_size': os.path.getsize(self.file_path),
            'file_path' : self.file_path
        }
        print(os.path.getsize(self.file_path), self.file_md5)
        header = self._json_package(header_dic)
        return header

    def _json_package(self, obj):
        """
        客户端发送信息打包成json并转换成二进制
        :param obj: 客户要发送的具体信息
        :return: 返回打包后的二进制信息
        """
        obj_json = json.dumps(obj)
        obj_bytes = obj_json.encode(settings.code)
        return obj_bytes

    def _file_encryption(self, file):
        """
        将明文的密码加密
        :param pss: 客户输入的密码
        :return: 加密后的密码
        """
        encryp_md5 = hashlib.md5()
        with open(file, 'rb') as f:
            for line in f:
                encryp_md5.update(line)
        self.file_md5 = encryp_md5.hexdigest()

    def _header_receive(self):
        """
        报头接收与拆包
        :return: 返回拆后的字典形式的报头
        """
        receiver = self.main_server.recv(settings.header_size)
        header_len = struct.unpack('i', receiver)[0]
        print(header_len)
        header = self.main_server.recv(header_len)
        header_dic = json.loads(header)
        return header_dic

    def download(self):
        '''
        文件下载功能，只能下载到用户本地的local文件夹（可以在客户端加上下载目录的选择）
        :return:
        '''
        try:
            self.file_path = '%s/%s' % (self.current_menu[-1], self.input_cmds[1])
            header = self._header_pack()
            # 把报头长度发给Client
            header_len = struct.pack('i', len(header))  # 制作报头长度的bytes
            self.main_server.send('200'.encode(settings.code))
            self.main_server.send(header_len)  # 发送报头的长度
            # 发送报头
            self.main_server.send(header)
            with open(self.file_path, 'rb') as f:
                for line in f:
                    self.main_server.send(line)
            print('%s传输成功' % self.input_cmds[1])
        except FileNotFoundError:
            self.main_server.send('999'.encode(settings.code))

    def upload(self):
        """
        文件上传功能，上传到客户定位的文件夹中
        :return:
        """
        self.header_dic = self._header_receive()
        file_size = self.header_dic['file_size']
        if int(self.config[self.user_name]['capacity']) < (file_size + int(self.config[self.user_name]['usage'])):
            #  可用空间判断，空间不足提示
            self.main_server.send('空间不足'.encode(settings.code))
            print('空间不足')
        else:
            self.main_server.send('True'.encode(settings.code))  # 返回信息，提示客户端可以开始上传
            self.filename = self.header_dic['file_name']

            count = 1
            while os.path.isfile(r'%s/%s' % (self.current_menu[-1], self.filename)):
                # 文件下载可能出现重名，重名时进行更改，不覆盖
                self.filename = '(%s)%s' % (count, self.filename)
                count += 1

            with open(r'%s/%s' % (self.current_menu[-1], self.filename), 'wb') as f:
                recv_size = 0
                while recv_size < file_size:
                    line = self.main_server.recv(settings.recv_size_each)
                    f.write(line)
                    recv_size += len(line)

            self._file_encryption(r'%s/%s' % (self.current_menu[-1], self.filename))

            if self.file_md5 == self.header_dic['md5']:
                # 文件一致性校验
                new_usage = os.path.getsize(r'%s/%s' % (self.current_menu[-1], self.filename))
                self.config.set(self.user_name, 'usage', str(new_usage))
                self.config.write(open(settings.accounts_dir, 'r+'))
                self.main_server.send('上传成功！'.encode(settings.code))
                print('上传成功！')
            else:
                self.main_server.send('发生错误，请重试'.encode(settings.code))

    def ls(self):
        """
        打印当前目录内所有文件，根目录在.../FTP/home/用户名
        :return:
        """
        menu_list = os.listdir(self.current_menu[-1])
        menu_list_package = self._json_package(menu_list)

        header_dic = {'file_size': len(menu_list_package)}
        header = self._json_package(header_dic)
        header_len = struct.pack('i', len(header))
        self.main_server.send(header_len)
        self.main_server.send(header)

        if not menu_list:
            return

        self.main_server.send(menu_list_package)

    def cd(self):
        """
        进入下一层菜单的指令, cd + 文件名
        :return:
        """
        folder = self.input_cmds[1]
        pointed_menu = r'%s/%s' % (self.current_menu[-1],folder)

        if not os.path.isdir(pointed_menu):
            self.main_server.send(('无文件夹%s' % folder).encode(settings.code))
            return

        self.current_menu.append(pointed_menu)
        self.main_server.send(('在%s目录下' % folder).encode(settings.code))
        print('在%s目录下' % folder)

    def back(self):
        """
        返回上一层目录，不可返回根目录的上层目录
        :return:
        """
        if len(self.current_menu) == 1:
            self.main_server.send('在根目录下，无法返回'.encode(settings.code))
            return

        if len(self.current_menu) > 1:
            del self.current_menu[-1]
            current_folder = os.path.basename(self.current_menu[-1])
            self.main_server.send(('在目录%s下' % current_folder).encode(settings.code))
            print('在目录%s下' % current_folder)

    def mkdir(self):
        """
        新建文件夹
        :return:
        """
        new_folder = self.input_cmds[1]

        count = 1
        while new_folder in os.listdir(self.current_menu[-1]):
            new_folder = '(%s)%s' % (count,new_folder)
            count += 1

        os.mkdir(r'%s/%s' % (self.current_menu[-1],new_folder))
        self.main_server.send(('文件夹%s创建成功' % new_folder).encode(settings.code))

    def delete(self):
        """
        删除文件或文件夹（会同时删除文件夹中的所有文件）
        :return:
        """
        delete_target = r'%s/%s' % (self.current_menu[-1], self.input_cmds[1])
        if self.input_cmds[1] not in os.listdir(self.current_menu[-1]):
            self.main_server.send('存在错误，对象不存在'.encode(settings.code))
            return

        try:
            os.remove(delete_target)
        except PermissionError:
            shutil.rmtree(delete_target)

        self.main_server.send(('%s已删除' % self.input_cmds[1]).encode(settings.code))

    def reconnection(self):
        """
        断点重连，当客户端在下载文件时，服务端出现突然断开时，在下次重新连接登陆后进行自动的断点续传
        :return:
        """
        reconnection_info = self.main_server.recv(settings.recv_size_each)

        if reconnection_info == b'False':
            return

        reconnection_dic = json.loads(reconnection_info)  # 字典(file_path, current_size, origin_size)
        file_path = reconnection_dic['file_path']
        file_origin_size = reconnection_dic['origin_size']
        broken_size = reconnection_dic['current_size']

        if os.path.isfile(file_path) and (os.path.getsize(file_path) == file_origin_size):
            self.main_server.send('200'.encode(settings.code))

            with open(file_path,'rb') as f:
                f.seek(broken_size)
                for line in f:
                    self.main_server.send(line)

            print('传输成功')
            return

        self.main_server.send('999'.encode(settings.code))