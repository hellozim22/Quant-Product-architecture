import requests
import json

def send_msg(content,robot_id):
    #robot_id = '06012b7785867b67e77efdd768da9cc727bc924f0b4a7a590614604261c19430'
    try:
        msg = {
            "msgtype": "text",
            "text": {"content": content }}

        Headers = {"Content-Type": "application/json ;charset=utf-8 "}
        url = 'https://oapi.dingtalk.com/robot/send?access_token=' + robot_id
        body = json.dumps(msg)
        requests.post(url, data=body, headers=Headers)
    except Exception as err:
        print('钉钉发送失败', err)



