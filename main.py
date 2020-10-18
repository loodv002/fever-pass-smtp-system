import time
import  csv
import requests
import smtplib
from email.mime.text import MIMEText

def isTeacher(personData):
    if personData[1] == '教職員' or personData[2] == '0':
        return True
    return False

with open('data.csv', 'r') as sysData:
    trf = list(csv.reader(sysData))

    checkTime = [list(map(int, i.split())) for i in trf[0][1:]]

    mail_host = trf[1][1]
    all_mail_user = trf[2][1:]
    all_mail_pass = trf[3][1:]
    all_sender = trf[4][1:]
    FPusername = trf[5][1]
    FPpassword = trf[6][1]
    directProcess = {'FALSE':False, 'TRUE':True}[trf[8][1]]
    sendingCheck = {'FALSE':False, 'TRUE':True}[trf[7][1]]
    
    if not sendingCheck:
        print('Sending system off')

while True:
    h, m = list(time.localtime())[3:5]
    doProcess = False

    for checkTimeSp in range(len(checkTime)):
        if checkTime[checkTimeSp] == [h, m]:
            doProcess = True
            break

    if not (doProcess or directProcess):
        print('time: %d:%d'%(h, m))
        
        time.sleep(60)
        continue

    mail_user = all_mail_user[checkTimeSp % len(all_mail_user)]
    mail_pass = all_mail_pass[checkTimeSp % len(all_mail_pass)]
    sender = all_sender[checkTimeSp % len(all_sender)]

    localDate = list(time.localtime())[:3]
    localTime = list(time.localtime())[:5]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}
    data = {'username':FPusername, 'password':FPpassword}
    url ='http://35.236.157.77/login' #'http://kksh.nctu.me/login'

    session = requests.Session()
    session.post(url,headers = headers,data = data)
    response = session.get('http://35.236.157.77/export?date=%4d-%04d-%04d&class='%tuple(localDate),headers = headers)
    response.encoding = 'utf-8'

    tempData = response.text.split('\n')[1:-1]

    print('request finish')

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host)  # 启用SSL发信, 端口一般是465
        smtpObj.login(mail_user, mail_pass)  # 登录验证
    except smtplib.SMTPException as errorMsg:
        with open('bugData.txt', 'a+') as bugData:
            bugData.write('%4d/%2d/%2d %2d:%2d:%2d'%(tuple(list(time.localtime())[:6])) + ' %s\n'%errorMsg)

    for i in range(len(tempData)):
        tempData[i] = tempData[i].split(',')

    fever = []
    noData = []

    for i in range(len(tempData)):
        if len(tempData[i]) == 3:
            noData.append(tempData[i])
        else:
            if float(tempData[i][3]) >= 37.5:
                fever.append(tempData[i])

    with open('authority.csv', 'r') as authority:
        for line in csv.reader(authority):
            if line[0] == '帳號':
                continue

            for i in range(len(fever)):
                if isTeacher(fever[i]):
                    if fever[i][0] == line[0]:
                        fever[i][0] = line[2]
                        break

            for i in range(len(noData)):
                if isTeacher(noData[i]):
                    if noData[i][0] == line[0]:
                        noData[i][0] = line[2]
                        break

    with open('authority.csv', 'r') as authority:                
        for line in csv.reader(authority):
            if line[0] == '帳號':
                continue
            
            studentFever = []
            studentNoData = []
            teacherFever = []
            teacherNoData = []

            if line[1] == 'self' or line[1] == 'principal':
                for i in fever:
                    if i[0] == line[2]:
                        if isTeacher(i):
                            teacherFever.append(i)
                        else:
                            studentFever.append(i)

                for i in noData:
                    if i[0] == line[2]:
                        if isTeacher(i):
                            teacherNoData.append(i)
                        else:
                            studentNoData.append(i)

            elif line[1] == 'all':
                for i in fever:
                    if isTeacher(i):
                        teacherFever.append(i)
                    else:
                        studentFever.append(i)

                for i in noData:
                    if isTeacher(i):
                        teacherNoData.append(i)
                    else:
                        studentNoData.append(i)
                
            elif line[1][:3] == 'lvl':
                for i in fever:
                    if i[1][0] == line[1][3]:
                        if isTeacher(i):
                            teacherFever.append(i)
                        else:
                            studentFever.append(i)

                for i in noData:
                    if i[1][0] == line[1][3]:
                        if isTeacher(i):
                            teacherNoData.append(i)
                        else:
                            studentNoData.append(i)

            elif line[1] == 'personnel':
                for i in fever:
                    if isTeacher(i):
                        teacherFever.append(i)

                for i in noData:
                    if isTeacher(i):
                        teacherNoData.append(i)
            else:
                for i in fever:
                    if i[1] == line[1]:
                        if isTeacher(i):
                            teacherFever.append(i)
                        else:
                            studentFever.append(i)
                for i in noData:
                    if i[1] == line[1]:
                        if isTeacher(i):
                            teacherNoData.append(i)
                        else:
                            studentNoData.append(i)

            if (len(teacherFever) == 0 and\
               len(studentFever) == 0 and\
               len(teacherNoData) == 0 and\
               len(studentNoData) == 0) and line[1] != 'principal':
                continue
            
            title = '中山附中fever pass自動訊息'  # 邮件主题
            content = '老師您好，截至%d年%d月%d日%d時%d分，您的下轄單位，\n'%tuple(localTime)

            if len(teacherNoData) != 0 or len(studentNoData) != 0:
                content = content + '共%d人未填報體溫，\n'%(len(studentNoData) + len(teacherNoData))
            else:
                content = content + '已全數完成體溫填報，\n'

            if len(teacherFever) != 0 or len(studentFever):
                content = content + '共%d人發燒。\n\n'%(len(studentFever) + len(teacherFever))
            else:
                content = content + '無人發燒。\n\n'
                      
            if len(teacherFever) != 0 or len(studentFever) != 0:
                content = content + '發燒人員 　單位 　座號 　體溫　\n'
                
                for i in teacherFever:
                    if i[1] == '教職員':
                        content = content + '%-6s　教職員 －－ %8s\n'%(i[0], i[3])
                    elif i[2] == '0':
                        content = content + '%-7s %-7s－－　 %-4s\n'%(i[0], i[1], i[3])

                content = content + '\n'

                for i in studentFever:
                    content = content + '%-10s %-8s %-4s%-8s\n'%(i[0], i[1], i[2], i[3])

                content = content + '\n'
                    
            if len(teacherNoData) != 0 or len(studentNoData) != 0:
                content = content + '未填人員 　單位 　座號\n'

                for i in teacherNoData:
                    if i[1] == '教職員':
                        content = content + '%-6s　教職員 －－\n'%(i[0])
                    elif i[2] == '0':
                        content = content + '%-7s %-7s－－\n'%(i[0], i[1])

                content = content + '\n'

                for i in studentNoData:
                    content = content + '%-10s %-8s%-4s\n'%(i[0], i[1], i[2])

                content = content + '\n'

            if line[1] in ['all', 'principal']:
                content += '全校完成率:%2.1f%%'%((1 - len(noData) / len(tempData)) * 100)
   
            message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
            message['From'] = "{}".format(sender)
            message['To'] = line[0] + '@nsysu.kksh.kh.edu.tw'
            message['Subject'] = title
            receivers = [line[0] + '@nsysu.kksh.kh.edu.tw']

            if sendingCheck:
                try:
                    time.sleep(5)
                    smtpObj.sendmail(sender, receivers, message.as_string())  # 发送
                    print(line[0] + ' mail has been send successfully.')
                except smtplib.SMTPException as errorMsg:
                    with open('bugData.txt', 'a+') as bugData:
                        bugData.write('%4d/%2d/%2d %2d:%2d:%2d'%(tuple(list(time.localtime())[:6])) + ' %s\n'%errorMsg)
            else:
                print(content)
                print(line[0] + ' mail has been send successfully.')
            
    smtpObj.quit()

    if directProcess:
        break
    else:
        time.sleep(60)
