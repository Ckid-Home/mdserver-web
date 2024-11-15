# coding:utf-8

# ---------------------------------------------------------------------------------
# MW-Linux面板
# ---------------------------------------------------------------------------------
# copyright (c) 2018-∞(https://github.com/midoks/mdserver-web) All rights reserved.
# ---------------------------------------------------------------------------------
# Author: midoks <midoks@163.com>
# ---------------------------------------------------------------------------------

import os

from flask import Blueprint, render_template
from flask import request


from admin import model
from admin.user_login_check import panel_login_required
import core.mw as mw
import utils.file as file

blueprint = Blueprint('files', __name__, url_prefix='/files', template_folder='../../templates/default')
@blueprint.route('/index', endpoint='index')
@panel_login_required
def index():
    return render_template('files.html')

# 获取文件内容
@blueprint.route('/get_body', endpoint='get_file_body', methods=['POST'])
@panel_login_required
def get_file_body():
    path = request.form.get('path', '')
    return file.getFileBody(path)

# 获取文件内容
@blueprint.route('/save_body', endpoint='save_body', methods=['POST'])
@panel_login_required
def save_body():
    path = request.form.get('path', '')
    data = request.form.get('data', '')
    encoding = request.form.get('encoding', '')
    if not os.path.exists(path):
        return mw.returnData(False, '文件不存在')
    try:
        if encoding == 'ascii':
            encoding = 'utf-8'

        data = data.encode(encoding, errors='ignore').decode(encoding)
        fp = open(path, 'w+', encoding=encoding)
        fp.write(data)
        fp.close()

        if path.find("web_conf") > 0:
            mw.restartWeb()
        mw.writeLog('文件管理', '文件[{1}]保存成功', (path,))
        return mw.returnData(True, '文件保存成功')
    except Exception as ex:
        return mw.returnData(False, '文件保存错误:' + str(ex))

# 获取文件内容(最新行数)
@blueprint.route('/get_last_body', endpoint='get_file_last_body', methods=['POST'])
@panel_login_required
def get_file_last_body():
    path = request.form.get('path', '')
    line = request.form.get('line', '100')

    if not os.path.exists(path):
        return mw.returnData(False, '文件不存在', (path,))

    try:
        data = mw.getLastLine(path, int(line))
        return mw.returnData(True, 'OK', data)
    except Exception as ex:
        return mw.returnData(False, '无法正确读取文件!' + str(ex))


# 获取文件列表
@blueprint.route('/get_dir', endpoint='get_dir', methods=['POST'])
@panel_login_required
def get_dir():
    path = request.form.get('path', '')
    if not os.path.exists(path):
        path = mw.getFatherDir() + '/wwwroot'
    search = request.args.get('search', '').strip().lower()
    search_all = request.args.get('all', '').strip().lower()
    page = request.args.get('p', '1').strip().lower()
    row = request.args.get('row', '10')
    order = request.form.get('order', '')

    if search_all == 'yes' and search != '':
        dir_list = file.getAllDirList(path, int(page), int(row),order, search)
    else:
        dir_list = file.getDirList(path, int(page), int(row),order, search)

    dir_list['page'] = mw.getPage({'p':page, 'row': row, 'tojs':'getFiles', 'count': dir_list['count']}, '1,2,3,4,5,6,7,8')
    return dir_list

# 获取站点日志目录
@blueprint.route('/get_dir_size', endpoint='get_dir_size', methods=['POST'])
@panel_login_required
def get_dir_size():
    path = request.form.get('path', '')
    size = file.getDirSize(path)
    return mw.returnData(True, mw.toSize(size))


# 删除文件
@blueprint.route('/delete', endpoint='delete', methods=['POST'])
@panel_login_required
def delete():
    path = request.form.get('path', '')
    return file.fileDelete(path)


# 删除文件
@blueprint.route('/delete_dir', endpoint='delete_dir', methods=['POST'])
@panel_login_required
def delete_dir():
    path = request.form.get('path', '')
    return file.dirDelete(path)


# 回收站文件
@blueprint.route('/get_recycle_bin', endpoint='get_recycle_bin', methods=['POST'])
@panel_login_required
def get_recycle_bin():
    return file.getRecycleBin()

# 回收站文件恢复
@blueprint.route('/re_recycle_bin', endpoint='re_recycle_bin', methods=['POST'])
@panel_login_required
def re_recycle_bin():
    path = request.form.get('path', '')
    return file.reRecycleBin(path)

# 回收站文件
@blueprint.route('/recycle_bin', endpoint='recycle_bin', methods=['POST'])
@panel_login_required
def recycle_bin():
    return file.toggleRecycleBin()
















