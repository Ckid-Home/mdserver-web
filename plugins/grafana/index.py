# coding:utf-8

import sys
import io
import os
import time
import re

web_dir = os.getcwd() + "/web"
if os.path.exists(web_dir):
    sys.path.append(web_dir)
    os.chdir(web_dir)

import core.mw as mw

app_debug = False
if mw.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'grafana'


def getPluginDir():
    return mw.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return mw.getServerDir() + '/' + getPluginName()


def getInitDFile():
    current_os = mw.getOs()
    if current_os == 'darwin':
        return '/tmp/' + getPluginName()

    if current_os.startswith('freebsd'):
        return '/etc/rc.d/' + getPluginName()

    return '/etc/init.d/' + getPluginName()


def getConf():
    path = getServerDir() + "/web_conf/nginx/vhost/zabbix.conf"
    return path


def getInitDTpl():
    path = getPluginDir() + "/init.d/" + getPluginName() + ".tpl"
    return path


def getArgs():
    args = sys.argv[3:]
    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        if t.strip() == '':
            tmp = []
        else:
            t = t.split(':')
            tmp[t[0]] = t[1]
        tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':')
            tmp[t[0]] = t[1]
    return tmp

def checkArgs(data, ck=[]):
    for i in range(len(ck)):
        if not ck[i] in data:
            return (False, mw.returnJson(False, '参数:(' + ck[i] + ')没有!'))
    return (True, mw.returnJson(True, 'ok'))

def getPidFile():
    file = getConf()
    content = mw.readFile(file)
    rep = r'pidfile\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()

def status():
    cmd = "ps aux|grep grafana |grep -v grep | grep -v python | grep -v mdserver-web | awk '{print $2}'"
    data = mw.execShell(cmd)
    if data[0] == '':
        return 'stop'
    return 'start'

def getInstallVerion():
    version_pl = getServerDir() + "/version.pl"
    version = mw.readFile(version_pl).strip()
    return version

def contentReplace(content):
    service_path = mw.getServerDir()
    content = content.replace('{$ROOT_PATH}', mw.getFatherDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$ZABBIX_ROOT}', '/usr/share/zabbix')
    content = content.replace('{$ZABBIX_PORT}', '18888')

    psdb = pSqliteDb('databases')
    db_pass = psdb.where('name = ?', ('zabbix',)).getField('password')
    content = content.replace('{$ZABBIX_DB_PORT}', getMySQLPort())
    content = content.replace('{$ZABBIX_DB_PASS}', db_pass)
    return content


def getMySQLConf():
    choose_mysql = getServerDir()+'/mysql.pl'
    if os.path.exists(choose_mysql):
        ver = mw.readFile(choose_mysql)
        return mw.getServerDir() + '/'+ver+'/etc/my.cnf'

    apt_path = mw.getServerDir() + '/mysql-apt/etc/my.cnf'
    if os.path.exists(apt_path):
        mw.writeFile(choose_mysql, 'mysql-apt')
        return apt_path

    yum_path = mw.getServerDir() + '/mysql-yum/etc/my.cnf'
    if os.path.exists(yum_path):
        mw.writeFile(choose_mysql, 'mysql-yum')
        return yum_path

    path = mw.getServerDir() + '/mysql/etc/my.cnf'
    if os.path.exists(path):
        mw.writeFile(choose_mysql, 'mysql')
        return path
    return path


def getMySQLPort():
    file = getMySQLConf()
    content = mw.readFile(file)
    rep = r'port\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()

def getMySQLSocketFile():
    file = getMySQLConf()
    content = mw.readFile(file)
    rep = r'socket\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()

def getMySQLBin():
    choose_mysql = getServerDir()+'/mysql.pl'
    ver = mw.readFile(choose_mysql)
    mysql_dir = mw.getServerDir() + '/'+ver

    if ver == 'mysql-apt':
        return '/www/server/mysql-apt/bin/usr/bin/mysql'
    if ver == 'mysql-yum':
        return '/www/server/mysql-yum/bin/usr/bin/mysql'
    return '/www/server/mysql/bin/mysql'

def getMySQLBinLink():
    choose_mysql = getServerDir()+'/mysql.pl'
    ver = mw.readFile(choose_mysql)
    mysql_dir = mw.getServerDir() + '/'+ver

    if ver == 'mysql-apt':
        return '/www/server/mysql-apt/bin/usr/bin/mysql -S /www/server/mysql-apt/mysql.sock'
    if ver == 'mysql-yum':
        return '/www/server/mysql-yum/bin/usr/bin/mysql -S /www/server/mysql-yum/mysql.sock'
    return '/www/server/mysql/bin/mysql -S /www/server/mysql/mysql.sock'

def pSqliteDb(dbname='databases'):
    choose_mysql = getServerDir()+'/mysql.pl'
    ver = mw.readFile(choose_mysql)

    mysql_dir = mw.getServerDir() + '/'+ver
    conn = mw.M(dbname).dbPos(mysql_dir, 'mysql')
    return conn


def pMysqlDb():
    # pymysql
    db = mw.getMyORM()
    db.setDbName('zabbix')
    db.setPort(getMySQLPort())
    db.setSocket(getMySQLSocketFile())
    db.setPwd(pSqliteDb('config').where('id=?', (1,)).getField('mysql_root'))
    return db


def getInstalledPhpConfDir():
    phpver = ["80","81","82","83","84"]
    php_type = ['php-apt','php-yum', 'php'];

    for pt in php_type:
        for ver in phpver:
            php_install_dir = mw.getServerDir() + '/'+ pt+'/'+ver
            if os.path.exists(php_install_dir):
                if pt == 'php-apt':
                    return pt + ver[0:1]+'.'+ver[1:2]
                if pt == 'php':
                    return pt + '-' + ver
                if pt == 'php-yum':
                    return pt + '-' + ver
                return pt + ver
    return 'php-80'

def isInstalledPhp():
    phpver = ["80","81","82","83","84","85"]
    php_type = ['php-apt','php-yum', 'php'];

    for pt in php_type:
        for ver in phpver:
            php_install_dir = mw.getServerDir() + '/'+ pt+'/'+ver
            if os.path.exists(php_install_dir):
                return True
    return False

def isInstalledMySQL():
    mysql_type = ['mysql-apt','mysql-yum', 'mysql'];
    for mt in mysql_type:
        mysql_install_dir = mw.getServerDir() + '/'+ mt
        if os.path.exists(mysql_install_dir):
            return True
    return False


def zabbixServerConf():
    ver = getInstallVerion()
    if ver == '6.0':
        return '/etc/zabbix_server.conf'
    return '/etc/zabbix/zabbix_server.conf'

def zabbixAgentConf():
    return '/etc/zabbix/zabbix_agentd.conf'

def initAgentConf():
    za_src_tpl = getPluginDir()+'/conf/zabbix_agentd.conf'
    za_dst_path = zabbixAgentConf()

    # zabbix_agent配置
    content = mw.readFile(za_src_tpl)
    content = contentReplace(content)
    mw.writeFile(za_dst_path, content)

def openPort():
    try:
        from utils.firewall import Firewall as MwFirewall
        MwFirewall.instance().addAcceptPort('3000', 'grafana', 'port')
        return port
    except Exception as e:
        return "Release failed {}".format(e)
    return True


def initDreplace():
    # 初始化OP配置
    init_file = getServerDir() + '/init.pl'
    if not os.path.exists(init_file):
        openPort()
        mw.writeFile(init_file, 'ok')
    return True


def gOp(method):
    initDreplace()

    data = mw.execShell('systemctl ' + method + ' grafana')
    mw.execShell('systemctl ' + method + ' grafana')
    if data[1] == '':
        return 'ok'
    return data[1]


def start():
    return gOp('start')

def stop():
    return gOp('stop')

def restart():
    return gOp('restart')

def reload():
    return gOp('reload')

def initdStatus():
    current_os = mw.getOs()
    if current_os == 'darwin':
        return "Apple Computer does not support"

    shell_cmd = 'systemctl status grafana | grep loaded | grep "enabled;"'
    data = mw.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    current_os = mw.getOs()
    if current_os == 'darwin':
        return "Apple Computer does not support"

    data = mw.execShell('systemctl enable grafana')
    if data[1] != '':
        return data[1]
    return 'ok'


def initdUinstall():
    current_os = mw.getOs()
    if current_os == 'darwin':
        return "Apple Computer does not support"

    data = mw.execShell('systemctl disable grafana')
    if data[1] != '':
        return data[1]
    return 'ok'

def runLog():
    zs_conf = zabbixServerConf()
    content = mw.readFile(zs_conf)

    rep = r'LogFile=\s*(.*)'
    tmp = re.search(rep, content)

    if tmp.groups():
        return tmp.groups()[0].strip()
    return '/var/log/zabbix/zabbix_server.log'

def zabbixAgentLog():
    za_conf = zabbixAgentConf()
    content = mw.readFile(za_conf)

    rep = r'LogFile=\s*(.*)'
    tmp = re.search(rep, content)

    if tmp.groups():
        return tmp.groups()[0].strip()
    return '/var/log/zabbix/zabbix_agentd.log'


def installPreInspection():
    cmd = "cat /etc/*-release | grep PRETTY_NAME |awk -F = '{print $2}' | awk -F '\"' '{print $2}'| awk '{print $1}'"
    sys = mw.execShell(cmd)


    cmd = "cat /etc/*-release | grep VERSION_ID | awk -F = '{print $2}' | awk -F '\"' '{print $2}'"
    sys_id = mw.execShell(cmd)

    sysName = sys[0].strip().lower()
    sysId = sys_id[0].strip().lower()

    # opensuse
    if not sysName in ['debian','centos','ubuntu','almalinux','rocky']:
        return '不支持该系统'

    if sysName == 'debian' and not sysId in ['12']:
        return '不支持,'+sysName+'['+sysId+'],仅支持debian12!'

    openresty_dir = mw.getServerDir() + "/openresty"
    if not os.path.exists(openresty_dir):
        return '需要安装Openresty插件'

    is_installed_php = isInstalledPhp()
    if not is_installed_php:
        return '需要安装PHP/PHP-APT/PHP-YUM插件,至少8.0!'


    is_installed_mysql = isInstalledMySQL()
    if not is_installed_mysql:
        return '需要安装MySQL/MySQL-APT/MySQL-YUM插件,至少8.0!'

    return 'ok'


def uninstallPreInspection():
    return 'ok'


if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print(status())
    elif func == 'start':
        print(start())
    elif func == 'stop':
        print(stop())
    elif func == 'restart':
        print(restart())
    elif func == 'reload':
        print(reload())
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUinstall())
    elif func == 'install_pre_inspection':
        print(installPreInspection())
    elif func == 'uninstall_pre_inspection':
        print(uninstallPreInspection())
    elif func == 'conf':
        print(zabbixNginxConf())
    elif func == 'run_log':
        print(runLog())
    elif func == 'zabbix_agent_log':
        print(zabbixAgentLog())
    else:
        print('error')
