"""
1.列出准确的文件上传列表
2.列出对应的远程路径
3.文件类型，文件名匹配
4.远程子目录创建
5.上传循环时间周期
6.生成log日志文件，日志保留多久
7.上传后本地文件是否保留
"""


import ftplib
import os
import time
import logging
import logging.handlers
from xml.dom.minidom import parse



#创建logger日志
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#Log Path
logpath = os.getcwd()+os.sep + 'Logs'+os.sep
if not os.path.exists(logpath):
    os.mkdir(logpath)    
logfile = logpath + 'jftplog'

#LOG FORMAT
LOG_FORMAT="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
log_handler=logging.handlers.TimedRotatingFileHandler(logfile,'D',1,15)
log_handler.suffix="_%Y%m%d.log"
log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(log_handler)



def readConfig():
    '''读取上传配置'''
    conf=parse(os.getcwd()+os.sep+'config.xml');#config文件与程序放在同一目录
    host=conf.getElementsByTagName("ServerIP")[0].firstChild.data
    username =conf.getElementsByTagName("UserID")[0].firstChild.data
    passwd=conf.getElementsByTagName("Passwd")[0].firstChild.data
    logBackupDay=int(conf.getElementsByTagName("LogBackupDay")[0].firstChild.data)
    uploadCheck=conf.getElementsByTagName("UploadCheck")[0].firstChild.data
    uploadLoopTime=int(conf.getElementsByTagName("Loop_Sec")[0].firstChild.data)
    localDir=conf.getElementsByTagName("LocalDirectory")[0].firstChild.data
    remoteDir=conf.getElementsByTagName("RemoteDirectory")[0].firstChild.data
    fileExtension=conf.getElementsByTagName("FileExtension")[0].firstChild.data
    fileNameContain=conf.getElementsByTagName("FileNameContain")[0].firstChild.data
    subDirCheck=conf.getElementsByTagName("SubDirectoryCheck")[0].firstChild.data
    subDirCreateCheck=conf.getElementsByTagName("SubDirectoryCreateCheck")[0].firstChild.data
    backupCheck=conf.getElementsByTagName("LocalFileBackupCheck")[0].firstChild.data
    fileCreateTime=int(conf.getElementsByTagName("FileCreateTime")[0].firstChild.data)
    conflist=[host,username,passwd,logBackupDay,uploadCheck,uploadLoopTime,
              localDir,remoteDir,fileExtension,fileNameContain,
              subDirCheck,subDirCreateCheck,backupCheck,fileCreateTime]
    return conflist

def strTobool(str2):
    '''字符串true和false转bool'''
    if str2.lower()=="true":
        return True
    elif str2.lower()=="false":
        return False
    else:
        raise Exception("Not bool value!")

def checkFileExtension(localfile,extension):
    '''
    检查文件名是否符合需要上传的文件类型
    extension为*时，无文件类型限制上传
    '''
    if extension=="*":
        return True
    elif localfile.endswith(extension):
        return True
    else:
        return False
    
def checkFileNameContains(localfile,filecontain):
    '''
    检查特定文件名的文件
	filecontain 为 * 时,不限制上传文件名
    '''
    if filecontain=="*":
        return True
    elif filecontain in localfile:
        return True
    else:
        return False

def checkFileModifiedTime(localfile,hour):
    '''只上传创建时间为hour小时内的文件'''
    if os.stat(localfile).st_ctime<time.time()-hour*3600:
        return False
    else:
        return True 
    
    
def upload(ftp,localFile,remoteFile):
    '''以二进制形式上传文件
    ftp.size()验证远程文件是否存在并且判断文件大小
    '''
    try:
        if ftp.size(remoteFile)==os.path.getsize(localFile):
            return
    except ftplib.error_perm as err:
        logger.warning("{0}.When upload file:{1}".format(err.args[0],remoteFile))
    except Exception as e:
        logger.warning("other error!")
    uf = open(localFile, 'rb')
    bufsize = 1024  # 设置缓冲器大小
    try:
        ftp.storbinary('STOR ' + remoteFile, uf, bufsize)
        logger.info("File has upload success:{}".format(remoteFile))
    except:
        logger.error("File Upload Fail!:{}".format(remoteFile))
    finally:
        uf.close()


def deleteLocalFile(deleteCheck,localfile):
    if not deleteCheck:
        os.remove(localfile)
        logger.info("Remove local file:{}".format(localfile))

def listFile(ftp,local,remote,subdircreatecheck,extension,filenamecontains,filecreatetime,localBackupCheck):
    '''递归调用出子文件或子文件夹 
    ftp FTP实例
    local 本地文件[夹]
    remote 远程文件[夹]
    subdircreatecheck 远程是否创建对应的子文件夹
    extension 文件类型
    filecontains 文件名必须包含
    filecreatetime 文件修改时间在多少小时内的
    localBackupCheck 本地文件是否保留
    '''
    for file in os.listdir(local):
        local2=os.path.join(local,file) #路径+文件名为 完整路径
        remote2=remote+'/'+file
        try:
            if not checkFileModifiedTime(local2,filecreatetime):
                continue
            if not subdircreatecheck:
                remote2=remote
            if os.path.isdir(local2):
                try:                         #验证ftp远程是否已有目录    
                    ftp.cwd(remote2)         #打开远程目录，无法打开则报异常，在异常处理里面创建远程目录
                except Exception as e:
                    logger.error("Fail to open directory.")
                    logger.info("Open directory: {} fail,so create dir.".format(remote2))                    
                    ftp.mkd(remote2)
                    logger.info("ItslocalDir:{}".format(local2))
                listFile(ftp,local2,remote2,subdircreatecheck,extension,filenamecontains,
                         filecreatetime,localBackupCheck)
            else:
                if checkFileExtension(local2,extension):
                    if checkFileNameContains(local2,filenamecontains):
                        remote2=remote+'/'+file
                        upload(ftp,local2,remote2)
                        deleteLocalFile(local2,localBackupCheck)
        except Exception as e:
            logger.error(e.args[0])

def deleteLog(days):
    '''删除多少天之前的日志文件'''
    for file2 in os.listdir(log_path):
        logfile=os.path.join(log_path,file2)
        if os.stat(logfile).st_ctime<time.time()-days*24*3600:
            os.remove(logfile)

            
if __name__ == '__main__':
    conf_list=readConfig()
    print(conf_list)
    
    host=conf_list[0]
    username=conf_list[1]
    passwd=conf_list[2]
    logBackupDay=conf_list[3]    
    uploadCheck=strTobool(conf_list[4])
    loopTime=conf_list[5]
    localpath=conf_list[6]
    remotepath=conf_list[7]    
    fileExtension=conf_list[8]
    fileNameContain=conf_list[9]
    subDirCheck=strTobool(conf_list[10])
    subDirCreateCheck=strTobool(conf_list[11])
    localFileBackupCheck=strTobool(conf_list[12])
    fileCreateTime=conf_list[13]
    
    
    logger.info("File Send Program Start!")
    while uploadCheck:
        logger.info("File Send Program LoopStart!")
        deleteLog(logBackupDay)
        f=ftplib.FTP(host)
        try:           
            f.login(username,passwd) #FTP用户登录            
            for file in os.listdir(localpath):
                local=os.path.join(localpath,file)
                remote=os.path.join(remotepath,file)
                if not checkFileModifiedTime(local,fileCreateTime):
                    continue
                if os.path.isdir(local):
                    if "." in local:
                        continue
                    if not subDirCheck:
                        logger.info("SubDir needn't upload!")
                        continue
                    if not subDirCreateCheck:
                        remote=remotepath
                    try:                        
                        f.cwd(remote)
                    except Exception as e:
                        logger.error("Fail to open remote directory.")
                        logger.info("Open directory:{} fail,so create dir.".format(remote))
                        f.mkd(remote)
                        logger.info("Its localDir={}".format(local))
                    listFile(f,local,remote,subDirCreateCheck,fileExtension,fileNameContain,
                             fileCreateTime,localFileBackupCheck)
                else:  
                    if checkFileExtension(local,fileExtension):
                        if checkFileNameContains(local,fileNameContain):
                            upload(f,local,remote)
                            deleteLocalFile(localFileBackupCheck,local)
        except Exception as e:
            logger.error(e)
            logger.error("Ftp upload fail!")            
        finally:
            f.quit()
        logger.info("Loop end,wait for next loop!")
        time.sleep(loopTime)
