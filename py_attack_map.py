# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: py_attack_map.py
 Time: 7/21/18
"""
import logging
import sys
import os
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor
from py_maxmind import query_city_from_geolite
from flask import Flask, render_template
from flask_restful import Api, Resource

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)

try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 6
except AssertionError:
    raise RuntimeError('py_attack_map only support Python 3.6+ !')

try:
    assert os.name != 'nt'
except AssertionError:
    raise RuntimeError('py_attack_map can not support Windows !')

pool = ThreadPoolExecutor(10)
app = Flask(__name__)
api = Api(app)

APP_PORT = 6789
AUTH_FILE_PATH = 'sample_auth.log'
DEBUG = False


# hydra -t 4 -l root -P 'worst-password.txt' ip ssh


def static_attack_by_cmd(filter_key: str = None, auth_file: str = None) -> str:
    """
    static attack by cmd
    :param filter_key:
    :param auth_file:
    :return:
    """
    filter_key = filter_key or 'Failed password for root'
    auth_file = auth_file or AUTH_FILE_PATH
    if not os.path.exists(auth_file):
        raise FileNotFoundError('auth log is not exists !')
    _proc1 = subprocess.Popen(['grep', filter_key, auth_file], shell=False, stdout=subprocess.PIPE)
    _proc2 = subprocess.Popen(['awk', "{print $11}"], shell=False, stdin=_proc1.stdout, stdout=subprocess.PIPE)
    _proc3 = subprocess.Popen(['sort'], shell=False, stdin=_proc2.stdout, stdout=subprocess.PIPE)
    _proc4 = subprocess.Popen(['uniq', '-c'], shell=False, stdin=_proc3.stdout, stdout=subprocess.PIPE)
    _proc5 = subprocess.Popen(['sort', '-nr'], shell=False, stdin=_proc4.stdout, stdout=subprocess.PIPE)
    _awk_out = _proc5.communicate()
    return _awk_out[0].decode('utf-8')


def generate_geojson_for_mapbox(raw_data_list: list):
    """
    :param raw_data_list:
    :return:
    """
    geojson_box = []
    for item in raw_data_list:
        if 'Failed' in item or item == '':
            continue
        if item.strip() == '':
            continue
        count_and_ip = item.strip().split(' ')
        count = count_and_ip[0]
        ip = count_and_ip[1]
        future = pool.submit(query_city_from_geolite, (ip))
        response = future.result()

        country_name = response.country.name or "UNKNOWN"
        country_chinese_name = '未知'
        if response.country is not None and response.country.names.get('zh-CN') is not None:
            country_chinese_name = response.country.names.get('zh-CN')
        city_name = response.city.name or "UNKNOWN"
        city_chinese_name = "未知"
        if response.city.names is not None and response.city.names.get('zh-CN') is not None:
            city_chinese_name = response.city.names.get('zh-CN')
        if city_chinese_name == '吴韩':
            city_chinese_name = '武汉'
        _point = {'type': 'Feature', 'geometry': {
            'type': 'Point',
            'coordinates': [response.location.longitude, response.location.latitude]
        }, 'properties': {
            'title': country_name + ' - ' + country_chinese_name,
            'description': ip + ' - ' + city_name + ' - ' + city_chinese_name + " Attack Counter: " + count,
            'marker-color': '#E74C3C',
            'marker-size': 'small',
            'marker-symbol': count
        }}
        geojson_box.append(_point)
        # print(response.country.name, response.country.names['zh-CN'], response.city.name,
        #       [response.location.longitude, response.location.latitude])
    return geojson_box


class PyAttackMapBox(Resource):
    def get(self):
        """
        restful api  /pyAttackMapBox
        :return:
        """
        static_raw_data = static_attack_by_cmd().split("\n")
        return generate_geojson_for_mapbox(raw_data_list=static_raw_data)


@app.route("/attack_map_view")
def map_box_template():
    return render_template("attack_map.html")


api.add_resource(PyAttackMapBox, '/pyAttackMapBox')


def cli():
    py_attack_map_version = '1.0 🐱'
    py_attack_map_author = 'Helixcs'
    py_attack_map_name = 'Py Attack Map'
    py_attack_map_desc = py_attack_map_name + "\t" + 'Author: ' + py_attack_map_author
    parser = argparse.ArgumentParser(prog=py_attack_map_name, description=py_attack_map_desc)
    parser.add_argument('-p', '--port', default=APP_PORT, help='port (default: %s)' % APP_PORT)
    parser.add_argument('-f', '--file', default='sample_auth.log', help='auth log file path (default: sample_auth.log)')
    parser.add_argument('-d', '--debug', default=DEBUG, help='is debug (default: %s)' % DEBUG)
    parser.add_argument('-v', '--version', action='version', version=py_attack_map_version)
    args = parser.parse_args()
    global AUTH_FILE_PATH
    AUTH_FILE_PATH = args.file
    app.run(debug=args.debug, port=args.port)


if __name__ == '__main__':
    cli()
