import sys
import threading
import schedule
import time
import os
import logging
import requests
import base64
import json
from aligo import set_config_folder, Aligo
from aligo.error import AligoFatalError
from datetime import datetime
from urllib.parse import parse_qs
from dataclass import DatClass

# 定义数据类
@dataclass
class Reward(DatClass):
    action: str = None
    background: str = None
    bottleId: str = None
    bottleName: str = None
    bottleShareId: str = None
    color: str = None
    description: str = None
    detailAction: str = None
    goodsId: int = None
    name: str = None
    notice: str = None
    subNotice: str = None

@dataclass
class Signinlogs(DatClass):
    calendarChinese: str = None
    calendarDay: str = None
    calendarMonth: str = None
    day: int = None
    icon: str = None
    isReward: bool = None
    notice: str = None
    pcAndWebIcon: str = None
    poster: str = None
    reward: Reward = None
    rewardAmount: int = None
    status: str = None
    themes: str = None
    type: str = None

@dataclass
class Result(DatClass):
    blessing: str = None
    description: str = None
    isReward: bool = None
    pcAndWebRewardCover: str = None
    rewardCover: str = None
    signInCount: int = None
    signInCover: str = None
    signInLogs: List[Signinlogs] = field(default_factory=list)
    signInRemindCover: str = None
    subject: str = None
    title: str = None

@dataclass
class SignInList(DatClass):
    arguments: str = None
    code: str = None
    maxResults: str = None
    message: str = None
    nextToken: str = None
    result: Result = None
    success: bool = None
    totalCount: str = None

@dataclass
class SignInReward(DatClass):
    arguments: str = None
    code: str = None
    maxResults: str = None
    message: str = None
    nextToken: str = None
    result: Reward = None
    success: bool = None
    totalCount: str = None

class CAligo(Aligo):
    V1_ACTIVITY_SIGN_IN_LIST = '/v1/activity/sign_in_list'
    V1_ACTIVITY_SIGN_IN_REWARD = '/v1/activity/sign_in_reward'

    def _sign_in(self, body: Dict = None):
        return self.post(
            CAligo.V1_ACTIVITY_SIGN_IN_LIST,
            host=Config.MEMBER_HOST,
            body=body, params={'_rx-s': 'mobile'}
        )

    def sign_in_list(self) -> SignInList:
        resp = self._sign_in({'isReward': True})
        return SignInList.from_str(resp.text)

    def sign_in_reward(self, day) -> SignInReward:
        resp = self.post(
            CAligo.V1_ACTIVITY_SIGN_IN_REWARD,
            host=Config.MEMBER_HOST,
            body={'signInDay': day},
            params={'_rx-s': 'mobile'}
        )
        return SignInReward.from_str(resp.text)

def signdaily():
    ali = CAligo(level=logging.ERROR)
    log = ali._auth.log
    sign_in_list = ali.sign_in_list()
    log.info('本月签到次数: %d', sign_in_list.result.signInCount)
    os.environ['SIGN_IN_COUNT'] = str(sign_in_list.result.signInCount)

    for i in sign_in_list.result.signInLogs:
        if i.isReward:
            continue
        if i.status == 'normal':
            sign_in_reward = ali.sign_in_reward(i.day)
            notice = sign_in_reward.result.notice
            log.info('签到成功: %s', notice)

# 配置日志记录
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.formatter = formatter
logger.info("Staring Aliyun Drive Backup Service ...")

# 获取环境变量
supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
config = '/data/'
set_config_folder(config)

# 读取 JSON 文件
with open(config+'options.json', 'r') as file:
    options_data = json.load(file)

for key, value in options_data.items():
    globals()[key] = value

def generate_html_listcloud():
    global user, space
    sign_in_count = os.environ.get('SIGN_IN_COUNT')
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>阿里云盘备份列表</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: white; }
            h1 { text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { width: 300px; background-color: #f2f2f2; }
            .info { margin-top: 10px; text-align: left; font-size: 14px; }
        </style>
    </head>
    <body>
        <h1>阿里云盘备份</h1>
        <h2>{user} 您的剩余空间还有: {space}</h2>
        <style>a {{ text-decoration: none; color: #808080; }}</style>
        <table>
            <thead>
                <tr>
                    <th>备份时间</th>
                    <th>备份名称</th>
                    <th>本地</th>
                    <th>云上</th>
                </tr>
            </thead>
            <tbody>
    """.format(user=user, space=space)
    
    for file_detail in backup_list():
        html_content += f"""
            <tr>
                <td>{file_detail['date']}</td>
                <td>{file_detail['name']}</td>
                <td>{file_detail['local']}</td>
                <td>{file_detail['cloud']}</td>
            </tr>
        """
    
    html_content += f"""
            </tbody>
        </table>
        <div class="info">
            {f"<h3>您本月已经签到 {sign_in_count} 次</h3>" if sign_in_count else ''}
            <p>每日备份时间：{backup_time}</p>
            <p>本地保留数量：{keep_days_local}</p>
            <p>云盘保存数量：{keep_days_cloud}</p>
            <p>如需修改备份设置，请在插件的配置页面进行修改。</p>
        </div>
    </body>
    </html>
    """

    return html_content

# 自定义请求处理程序
class BackupFilesHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if "404" in format or "500" in format:
            super().log_message(format, *args)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        refresh_tag = '<meta http-equiv="refresh" content="60">'
        html_content = generate_html_listcloud()
        content = f"{refresh_tag}{html_content}"
        self.wfile.write(content.encode())

    def do_POST(self):
        post_data = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8')
        post_params = parse_qs(post_data)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        file_id = post_params.get('file_id', [''])[0]
        message = f"Received POST data. File ID: {file_id}"
        self.wfile.write(message.encode())

def start_http_server():
    server_address = ('0.0.0.0', 7333)
    httpd = HTTPServer(server_address, BackupFilesHandler)
    logging.info("在端口 8080 上启动 HTTP 服务器...")
    httpd.serve_forever()

if __name__ == "__main__":
    t1 = threading.Thread(target=signdaily)
    t2 = threading.Thread(target=start_http_server)
    
    t1.start()
    t2.start()
    
    schedule.every().day.at("00:00").do(signdaily)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
