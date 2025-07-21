# coding:utf-8

import sys
import io
import os
import time
import re
import string
import subprocess

web_dir = os.getcwd() + "/web"
if os.path.exists(web_dir):
    sys.path.append(web_dir)
    os.chdir(web_dir)

import core.mw as mw

app_debug = False
if mw.isAppleSystem():
    app_debug = True

def getPluginName():
    return 'manticoresearch'

def getPluginDir():
    return mw.getPluginDir() + '/' + getPluginName()

sys.path.append(getPluginDir() +"/class")

def getServerDir():
    return mw.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getConfTpl():
    path = getPluginDir() + "/conf/manticore.conf"
    return path


def getConf():
    path = "/etc/manticoresearch/manticore.conf"
    return path


def getInitDTpl():
    path = getPluginDir() + "/init.d/" + getPluginName() + ".tpl"
    return path


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        t = t.split(':')
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


def configTpl():
    path = getPluginDir() + '/tpl'
    pathFile = os.listdir(path)
    tmp = []
    for one in pathFile:
        file = path + '/' + one
        tmp.append(file)
    return mw.getJson(tmp)


def readConfigTpl():
    args = getArgs()
    data = checkArgs(args, ['file'])
    if not data[0]:
        return data[1]

    content = mw.readFile(args['file'])
    content = contentReplace(content)
    return mw.returnJson(True, 'ok', content)


def contentReplace(content):
    service_path = mw.getServerDir()
    content = content.replace('{$ROOT_PATH}', mw.getFatherDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$SERVER_APP}', service_path + '/'+getPluginName())
    return content


def status():
    cmd = "ps -ef|grep manticore |grep -v grep | grep -v mdserver-web | awk '{print $2}'"
    data = mw.execShell(cmd)
    # print(data)
    if data[0] == '':
        return 'stop'
    return 'start'


def mkdirAll():
    content = mw.readFile(getConf())
    rep = r'path\s*=\s*(.*)'
    p = re.compile(rep)
    tmp = p.findall(content)

    for x in tmp:
        if x.find('binlog') != -1:
            mw.execShell('mkdir -p ' + x)
        else:
            mw.execShell('mkdir -p ' + os.path.dirname(x))

def initDreplace():

    dirs_list = [
        "/var/log/manticore",
        "/var/run/manticore",
        "/var/lib/manticore"
    ]

    for d in dirs_list:
        if not os.path.exists(d):
            mw.execShell('mkdir -p ' + d)

    # config replace
    conf_bin = getConf()
    if not os.path.exists(conf_bin):
        conf_content = mw.readFile(getConfTpl())
        conf_content = contentReplace(conf_content)
        mw.writeFile(getConf(), conf_content)


    mkdirAll()
    return "ok"


def checkIndexSph():
    content = mw.readFile(getConf())
    rep = r'path\s*=\s*(.*)'
    p = re.compile(rep)
    tmp = p.findall(content)
    for x in tmp:
        if x.find('binlog') != -1:
            continue
        else:
            p = x + '.sph'
            if os.path.exists(p):
                return False
    return True

def mcsOp(method):
    initDreplace()
    data = mw.execShell('systemctl ' + method + ' manticore')
    if data[1] == '':
        return 'ok'
    return 'fail'


def start():
    # import tool_cron
    # tool_cron.createBgTask()
    return mcsOp('start')


def stop():
    # import tool_cron
    # tool_cron.removeBgTask()
    return mcsOp('stop')


def restart():
    return mcsOp('restart')


def reload():
    return mcsOp('reload')


def rebuild():
    file = initDreplace()
    cmd = file + ' rebuild'
    data = mw.execShell(cmd)
    if data[0].find('successfully')<0:
        return data[0].replace("\n","<br/>")
    return 'ok'


def initdStatus():
    shell_cmd = 'systemctl status manticore | grep loaded | grep "enabled;"'
    data = mw.execShell(shell_cmd)
    if data[0] == '':
        return 'fail'
    return 'ok'


def initdInstall():
    mw.execShell('systemctl enable manticore')
    return 'ok'


def initdUinstall():
    mw.execShell('systemctl disable manticore')
    return 'ok'


def runLog():
    path = getConf()
    content = mw.readFile(path)
    rep = r'log\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0]


def getMainPort():
    path = getConf()
    content = mw.readFile(path)
    rep = r'listen\s*=\s*(.*)'
    conf = re.search(rep, content)
    port_line = conf.groups()[0]
    return port_line.split(":")[1]

def getMysqlPort():
    path = getConf()
    content = mw.readFile(path)
    rep = r'listen\s*=\s*(.*):mysql'
    conf = re.search(rep, content)
    port_line = conf.groups()[0]
    return port_line.split(":")[1]

def getHttpPort():
    path = getConf()
    content = mw.readFile(path)
    rep = r'listen\s*=\s*(.*):http'
    conf = re.search(rep, content)
    port_line = conf.groups()[0]
    return port_line.split(":")[1]


def queryLog():
    path = getConf()
    content = mw.readFile(path)
    rep = r'query_log\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0]


def runStatus():
    s = status()
    if s != 'start':
        return mw.returnJson(False, '没有启动程序')

    port = getHttpPort()
    url = "http://127.0.0.1:"+port+"/status"
    data = mw.httpGet(url)
    return mw.returnJson(True, 'ok', data)


def sphinxConfParse():
    file = getConf()
    bin_dir = getServerDir()
    content = mw.readFile(file)
    rep = r'index\s(.*)'
    sindex = re.findall(rep, content)
    indexlen = len(sindex)
    cmd = {}
    cmd['cmd'] = "indexer -c " + getConf()

    cmd['index'] = []
    cmd_index = []
    cmd_delta = []
    if indexlen > 0:
        for x in range(indexlen):
            name = sindex[x].strip()
            if name == '':
                continue
            if  name.find(':') != -1:
                cmd_delta.append(name.strip())
            else:
                cmd_index.append(name.strip())

    # print(cmd_index)
    # print(cmd_delta)

    for ci in cmd_index:
        val = {}
        val['index'] = ci

        for cd in cmd_delta:
            cd = cd.replace(" ", '')
            if cd.find(":"+ci) > -1:
                val['delta'] = cd.split(":")[0].strip()
                break

        cmd['index'].append(val)
    return cmd


def sphinxCmd():
    data = sphinxConfParse()
    if 'index' in data:
        return mw.returnJson(True, 'ok', data)
    else:
        return mw.returnJson(False, 'no index')

def makeDbToSphinxTest():        
    conf_file = getConf()
    import  sphinx_make
    sph_make = sphinx_make.sphinxMake()
    conf = sph_make.makeSqlToSphinxAll()

    mw.writeFile(conf_file,conf)
    print(conf)
    # makeSqlToSphinxTable()
    return True

def makeDbToSphinx():
    args = getArgs()
    check = checkArgs(args, ['db','tables','is_delta','is_cover'])
    if not check[0]:
        return check[1]

    db = args['db']
    tables = args['tables']
    is_delta = args['is_delta']
    is_cover = args['is_cover']

    if is_cover != 'yes':
        return mw.returnJson(False,'暂时仅支持覆盖!')

    sph_file = getConf()

    import  sphinx_make
    sph_make = sphinx_make.sphinxMake()

    version_pl = getServerDir() + "/version.pl"
    if os.path.exists(version_pl):
        version = mw.readFile(version_pl).strip()
        sph_make.setVersion(version)

    if not sph_make.checkDbName(db):
        return mw.returnJson(False,'保留数据库名称,不可用!')
    is_delta_bool = False
    if is_delta == 'yes':
        is_delta_bool = True
    if is_cover == 'yes':
        tables = tables.split(',')
        content = sph_make.makeSqlToSphinx(db, tables, is_delta_bool)
        mw.writeFile(sph_file,content)
        return mw.returnJson(True,'设置成功!')

    return mw.returnJson(True,'测试中')


# 全量更新
def updateAll():
    data = sphinxConfParse()
    cmd = data['cmd']
    if not 'index' in data:
        return '无更新'
    index = data['index']

    for x in range(len(index)):
        cmd_index = cmd + ' ' + index[x]['index'] + ' --rotate'
        print(cmd_index)
        os.system(cmd_index)
    return ''

#增量更新
def updateDelta():
    data = sphinxConfParse()
    cmd = data['cmd']
    if not 'index' in data:
        return '无更新'
    index = data['index']

    for x in range(len(index)):
        if 'delta' in index[x]:
            cmd_index = cmd + ' ' + index[x]['delta'] + ' --rotate'
            print(cmd_index)
            os.system(cmd_index)

            cmd_index_merge = cmd + ' --merge ' + index[x]['index'] + ' ' + index[x]['delta'] + ' --rotate'
            print(cmd_index_merge)
            os.system(cmd_index_merge)
        else:
            print(index[x]['index'],'no delta')

    return ''

def installPreInspection(version):
    if mw.isAppleSystem():
        return '不支持mac系统'
    return 'ok'

if __name__ == "__main__":
    version = "3.1.1"
    version_pl = getServerDir() + "/version.pl"
    if os.path.exists(version_pl):
        version = mw.readFile(version_pl).strip()

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
    elif func == 'rebuild':
        print(rebuild())
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUinstall())
    elif func == 'install_pre_inspection':
        print(installPreInspection(version))
    elif func == 'conf':
        print(getConf())
    elif func == 'config_tpl':
        print(configTpl())
    elif func == 'read_config_tpl':
        print(readConfigTpl())
    elif func == 'run_log':
        print(runLog())
    elif func == 'query_log':
        print(queryLog())
    elif func == 'run_status':
        print(runStatus())
    elif func == 'sphinx_cmd':
        print(sphinxCmd())
    elif func == 'db_to_sphinx':
        print(makeDbToSphinx())
    elif func == 'update_all':
        print(updateAll())
    elif func == 'update_delta':
        print(updateDelta())
    else:
        print('error')
