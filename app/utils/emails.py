import smtplib
from flask import current_app
from loguru import logger

# 发送邮箱验证码
def send_msg(email, msg):
    try:
        # 邮件操作
        msg = msg
        msg['Subject'] = '邮箱验证码'
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = email

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(e)
        return False