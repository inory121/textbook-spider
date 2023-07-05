import os
import shutil
import sys
import time

from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication
from bs4 import BeautifulSoup
import requests
import img2pdf


class MyThread(QThread):
    result = pyqtSignal(str)

    def __init__(self, start_page, end_page, book_id):
        super().__init__()
        self.start_page = start_page
        self.end_page = end_page
        self.book_id = book_id

    def run(self):
        start_page = int(self.start_page)
        end_page = int(self.end_page)
        book_id = int(self.book_id)
        # 获取书籍名称
        url = 'https://book.pep.com.cn/%d/mobile/index.html' % book_id
        res = requests.get(url)
        title = None
        if res.status_code == 200:
            title = BeautifulSoup(res.content, "html.parser").find("title").text
            print(title + 'title')
        else:
            self.result.emit('书籍信息获取失败!')
            return

        # 下载图片到imgs文件夹
        for i in range(start_page, end_page + 1):
            url = 'https://book.pep.com.cn/{}/files/mobile/{}.jpg?230217165451'.format(book_id, i)
            self.result.emit('正在下载《{}》第{}张图片...'.format(title, i))
            print('正在下载《{}》第{}张图片...'.format(title, i))
            r = requests.get(url, stream=True)
            print(r.status_code)
            if not os.path.exists('./imgs'):
                os.mkdir('./imgs')
            if r.status_code == 200:
                with open('./imgs/img_{}.jpg'.format(i), 'wb') as f:
                    f.write(r.content)
                    print("done")
            else:
                print("Error")
                self.result.emit("获取图片地址失败!")
            del r

        # 图片转pdf
        dirname = "./imgs"
        save_pdf_file = "%s.pdf" % title
        with open(save_pdf_file, "wb") as f:
            imgs = []
            for fname in os.listdir(dirname):
                path = os.path.join(dirname, fname)
                if os.path.isdir(path):
                    continue
                imgs.append(path)
            imgs.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
            print(imgs)
            f.write(img2pdf.convert(imgs))
        self.result.emit("转换成功！")
        print("转换成功！")
        shutil.rmtree('./imgs')
        os.mkdir('./imgs')


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.ui = uic.loadUi('./myui.ui')
        self.start_page = self.ui.start_page
        self.end_page = self.ui.end_page
        self.book_id = self.ui.book_id
        self.result_show = self.ui.result_show
        start_btn = self.ui.start_btn
        stop_btn = self.ui.stop_btn
        start_btn.clicked.connect(self.start_download)
        stop_btn.clicked.connect(self.stop_download)

    def start_download(self):
        start_page = self.start_page.text()
        end_page = self.end_page.text()
        book_id = self.book_id.text()
        self.start_thread = MyThread(start_page, end_page, book_id)
        self.start_thread.result.connect(self.update_text)
        self.start_thread.start()

    def stop_download(self):
        self.start_thread.terminate()

    def update_text(self, data):
        self.result_show.append(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MyWindow()
    w.ui.show()
    app.exec_()
