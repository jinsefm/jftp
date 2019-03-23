# jftp

A ftp program auto to upload file by time.



## Python - FtpLib模块应用

> 工厂中有这样的应用场景: 需要不间断地把设备电脑生成的数据文件上传到远程文件存储服务器NAS中。

在python自带的标准库中找到[**ftplib**](http://coverage.livinglogic.de/Lib/ftplib.py.html)模块，可以帮助实现文件的上传。

场景功能的实现需要做到以下几点:

- 给定本地路径，上传范围是否包含子文件夹及其文件

- 限定或不限定 哪些文件类型的文件，文件名包含哪些字符串的文件

- 文件上传后，本地是否要保留

- 扫完一次本地路径，进行下次循环的间隔周期

- 生成log日志方便查看报错与已上传的文件，日志文件保留多久之后要删除

思路是这样子，以上内容设计成一个config 文件进行管控。

## 1.config.xml文件设置

```jsx


  10.12.x.x
  user1
  123456

  10
  TRUE
  30
  D:\000\Desktop\TEST\
  /DATA/TEST/
  *
  *    

  TRUE
  TRUE
  TRUE
  24
```

- **LogBackupDay** 日志保留天数

- **UploadCheck** 是否开启上传

- **Loop_Sec** 扫描循环周期

- **LocalDirectory** 本地路径，结尾必须有路径分隔符

- **RemoteDirectory** 远程路径，结尾必须有路径分隔符

- **FileExtension** 文件类型，jpg,txt,py,log等等，为*时不限制文件类型

- **FileNameContain** 文件名字符串 ， 文件名包含哪些字符串的文件，为*时不限制文件名

- **SubDirectoryCheck** 子文件夹的文件是否上传

- **SubDirectoryCreateCheck** 远程路径是否创建和本地路径一样的文件夹

- **LocalFileBackupCheck** 本地文件是否保留

- **FIleCreateTime** 扫描本地路径中创建时间为多少个小时内的文件或文件夹

以下是读取config.xml的代码

```python
from xml.dom.minidom import parse

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
    fileNameContain=conf.getElementsByTagName("TxtFileNameContain")[0].firstChild.data
    subDirCheck=conf.getElementsByTagName("SubDirectoryCheck")[0].firstChild.data
    subDirCreateCheck=conf.getElementsByTagName("SubDirectoryCreateCheck")[0].firstChild.data
    backupCheck=conf.getElementsByTagName("LocalFileBackupCheck")[0].firstChild.data
    fileCreateTime=int(conf.getElementsByTagName("FileCreateTime")[0].firstChild.data)

    conflist=[host,username,passwd,logBackupDay,uploadCheck,uploadLoopTime,
              localDir,remoteDir,fileExtension,fileNameContain,
              subDirCheck,subDirCreateCheck,backupCheck,fileCreateTime]
    return conflist
```

## 2.相关逻辑实现

- **文件类型及文件名检验**

```python
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
```

- **文件上传之后，本地是否保留**

  ```python
  def deleteLocalFile(deleteCheck,localfile):
      if not deleteCheck:
          os.remove(localfile)
          logger.info("Remove local file:{}".format(localfile))
  ```

- **只上传创建时间为N个小时内的文件或文件夹**

```python
def checkFileModifiedTime(localfile,hour):
    '''只上传创建时间为hour小时内的文件'''
    if os.stat(localfile).st_ctime
```

- **生成日志，日志文件保留多久**

```python
#创建logger日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)
#filehandler
rq = time.strftime('%Y%m%d', time.localtime(time.time()))
log_path = os.getcwd()+os.sep + 'Logs'+os.sep
if not os.path.exists(log_path):
    os.mkdir(log_path)
log_name = log_path + rq + '.log'
logfile = log_name
fh = logging.FileHandler(logfile, mode='w')
fh.setLevel(logging.DEBUG)
#filehandler输出格式
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
```

```python
def deleteLog(days):
    '''删除多少天之前的日志文件'''
    for file2 in os.listdir(log_path):
        logfile=os.path.join(log_path,file2)
        if os.stat(logfile).st_ctime
```

- **展开子文件夹及相关判断逻辑**

  ```python
  def listFile(ftp,local,remote,subdircreatecheck,extension,filenamecontains,filecreatetime,
  localBackupCheck):
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
  ```

- **上传及异常检验**

  远程文件已存在并且大小与本地一致时无需上传，使用ftp.size()对比远程文件与本地文件大小即可，出现异常表明远程文件不存在。

  ```python
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
  ```

- **周期循环**

  ```python
  logger.info("File Send Program Start!")
  while uploadCheck:
  
      logger.info("File Send Program LoopStart!")
  
      deleteLog(logBackupDay)
  
      f=ftplib.FTP(host)
      try:
          ###
      except:
          ###
      finally:
          f.quit()
      logger.info("Loop end,wait for next loop!")
      time.sleep(loopTime)
  ```

## 3.打包exe文件

[pyinstaller库打包](https://blog.csdn.net/jinsefm/article/details/80645202)

值的注意的是，64位python环境下打包的exe不能在32位的Win7、xp运行。最后使用32位的python环境进行打包。

`pyinstaller -i jftp.ico -F Jftp.py -w`
