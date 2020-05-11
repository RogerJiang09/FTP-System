import struct, json, hashlib, os, shelve


class Main:
    """
    response_list是客户端传来的数字对应的文字内容
    与客户端对文件进行操作的具体交互方式
    """
    response_list = {
        '200': '文件存在，准备传输',
        '300': '文件夹为空',
        '999': '存在错误，文件不存在',
    }

    def __init__(self, obj):
        self.recv_size_each = obj.recv_size_each
        self.header_size = 4
        self.code = 'utf-8'
        self.shelve_obj = shelve.open('file_record_db')
        self.client = obj.client
        self.reconnection()

        while True:
            self.input_cmds = self._input_verify().split()
            self.path = obj.file_path  # /Users/roger/Desktop/FTP/client/local
            self.menu_operation_list = ['mkdir', 'cd', 'back', 'delete']  # 文件操作目录统合
            if self.input_cmds[0] in self.menu_operation_list:
                self.input_cmds[0] = 'menu_operations'
            getattr(self, self.input_cmds[0])()

    def _input_verify(self):
        """
        判断用户输入的合法性，判断并根据客户端回复进行下一步操作
        :return:
        """
        while True:
            cmds = input('>>: ')

            if cmds.lower() == 'exit':
                exit('期待您的再次使用！')

            self.client.send(cmds.encode(self.code))
            feedback = self.client.recv(self.recv_size_each).decode(self.code)
            if feedback == 'receive':
                return cmds
            elif not feedback:
                exit('客户端断开名，请联系管理员！')
            else:
                print('输入不符合规范，请重新输入！')
                self._help()

    def _help(self):
        """
        帮助信息
        """
        msg = '''
        ***FTP系统操作以操作+文件名进行对应操作***
        上传数据到当前目录：        upload a.txt
        下载数据：                download a.txt
        打印当前目录：                  ls
        进入当前目录下文件夹:           cd a
        在当前目录下生层文件夹:        mkdir a
        删除当前目录下文件夹或文件:    delete a
        返回上层目录:                  back
        退出FTP系统：                  exit
        '''
        print(msg)

    def _header_pack(self):
        """
        报头打包
        :return:  返回用json打包后的报头
        """
        self._file_encryption(self.file_path)
        header_dic = {
            'file_name': self.input_cmds[1],
            'md5': self.file_md5,
            'file_size': os.path.getsize(self.file_path)
        }
        header = self._json_package(header_dic)
        return header

    def _json_package(self, obj):
        """
        客户端发送信息打包成json并转换成二进制
        :param obj: 客户要发送的具体信息
        :return: 返回打包后的二进制信息
        """
        obj_json = json.dumps(obj)
        obj_bytes = obj_json.encode(self.code)
        return obj_bytes

    def _header_receive(self):
        """
        报头接收与拆包
        :return: 返回拆后的字典形式的报头
        """
        receiver = self.client.recv(self.header_size)
        header_len = struct.unpack('i', receiver)[0]
        header = self.client.recv(header_len)
        header_info = json.loads(header)
        return header_info

    def _file_encryption(self, file):
        """
        将明文的密码加密
        :param file: 客户输入的密码
        :return: 加密后的密码
        """
        encryp_md5 = hashlib.md5()
        with open(file, 'rb') as f:
            for line in f:
                encryp_md5.update(line)
        self.file_md5 = encryp_md5.hexdigest()

    def _progress_bar(self, total_size):
        """
        进度条显示生成器
        :param total_size: 文件的总大小
        :return:
        """
        last_percentage = 0
        while True:
            received_size = yield
            current_percentage = int(received_size / total_size * 100)

            if current_percentage > last_percentage:
                print('#' * int(current_percentage / 2) + '{percentage}%'.format(percentage=current_percentage),
                      end='\r', flush=True)
                last_percentage = current_percentage

    def download(self):
        """
        文件下载功能，并记录文件的大小，目标地址，下载地址，为断点续传提供信息，下载内容自动存放在local文件夹中(可加入自选目录)
        :return:
        """
        confirmation = self.client.recv(3).decode(self.code)  # 文件存在行回传信息
        if confirmation == '200':
            print(self.response_list[confirmation])
            self.header_dic = self._header_receive()
            file_size = self.header_dic['file_size']
            self.filename = self.header_dic['file_name']
            self.server_path= self.header_dic['file_path']  # 服务端中文件的地址

            count = 1
            while os.path.isfile(r'%s/%s' % (self.path, self.filename)):
                # 重名文件处理
                self.filename = '(%s)%s' % (count, self.filename)
                count += 1

            self.shelve_obj[r'%s/%s' % (self.path, self.filename)] = (file_size, self.server_path)
            with open(r'%s/%s' % (self.path, self.filename), 'wb') as f:
                recv_size = 0

                progress_generator = self._progress_bar(file_size)
                progress_generator.__next__()

                while recv_size < file_size:
                    line = self.client.recv(self.recv_size_each)
                    if not line: break
                    f.write(line)
                    recv_size += len(line)
                    progress_generator.send(recv_size)

            self._file_encryption(r'%s/%s' % (self.path, self.filename))

            if self.file_md5 == self.header_dic['md5']:
                del self.shelve_obj[r'%s/%s' % (self.path, self.filename)]  # 下载成功后删除存储的路径信息
                print('下载成功'.center(50, '-'))
            else:
                exit('发生错误，请重试！')

        elif confirmation == '999':
            print(self.response_list[confirmation])

    def upload(self):
        """
        文件上传功能，只可从local文件加提取上传到自己的客户端上home目录下
        :return:
        """
        self.file_path = r'%s/%s' % (self.path, self.input_cmds[1])
        if os.path.isfile(self.file_path):
            header = self._header_pack()
            # 把报头长度发给Server
            header_len = struct.pack('i', len(header))  # 制作报头长度的bytes
            self.client.send(header_len)  # 发送报头的长度
            # 发送报头
            self.client.send(header)
            response = self.client.recv(self.recv_size_each).decode(self.code)
            if response == 'True':
                file_size = os.path.getsize(self.file_path)
                upload_size = 0

                progress_generator = self._progress_bar(file_size)
                progress_generator.__next__()

                with open(self.file_path, 'rb') as f:
                    for line in f:
                        self.client.send(line)
                        upload_size += len(line)
                        progress_generator.send(upload_size)

                response = self.client.recv(self.recv_size_each).decode(self.code)
                print(('%s%s' % (self.input_cmds[1], response)).center(50, '-'))
            else:
                print(response)
        else:
            print(self.response_list['999'])

    def ls(self):
        """
        显示当前所在文件夹中的所有文件
        :return:
        """
        self.header_dic = self._header_receive()
        info_size = self.header_dic['file_size']
        if info_size == 2:  # 列表符
            print('文件夹为空')
            return

        recv_size = 0
        menu_list_package = b''
        while recv_size < info_size:
            line = self.client.recv(self.recv_size_each)
            recv_size += len(line)
            menu_list_package += line

        menu_list = json.loads(menu_list_package)
        for i in menu_list:
            print(i)

    def menu_operations(self):
        """
        根据服务端回传数据进行输出打印
        :return:
        """
        response = self.client.recv(self.recv_size_each)
        print(response.decode(self.code))

    def reconnection(self):
        """
        断点重连，当客户端在下载文件时，服务端出现突然断开时，在下次重新连接登陆后进行自动的断点续传
        :return:
        """
        if not list(self.shelve_obj.keys()):
            self.client.send('False'.encode(self.code))
            return
        path_record = list(self.shelve_obj.keys())[0]  # 因为现在只支持单个文件单操作，所以只可能存在一个文件有断点
        file_size = self.shelve_obj[path_record][0]  # 文件格式是(大小，服务端路径)
        broken_size = os.path.getsize(path_record)
        if os.path.isfile(path_record) and (broken_size < file_size):
            reconnection_dic = {
                'file_path': self.shelve_obj[path_record][1],
                'current_size': broken_size,
                'origin_size' : file_size
            }
            reconnection_info = self._json_package(reconnection_dic)
            self.client.send(reconnection_info)
            confirmation = self.client.recv(3).decode(self.code)

            if confirmation == '999':
                print(self.response_list['999'])
                return

            print(self.response_list[confirmation])

            with open(path_record , 'ab') as f:

                progress_generator = self._progress_bar(file_size)
                progress_generator.__next__()

                while broken_size < file_size:
                    line = self.client.recv(self.recv_size_each)
                    f.write(line)
                    broken_size += len(line)
                    progress_generator.send(broken_size)

            print('%s文件续传成功' % os.path.basename(path_record))
            del self.shelve_obj[path_record]  # 续传成功后删除数据库中对应信息