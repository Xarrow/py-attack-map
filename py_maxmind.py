# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: py_maxmind.py
 Time: 7/22/18
"""
import geoip2.database as GeoIp2DB

reader = GeoIp2DB.Reader('GeoLite2-City_20180703/GeoLite2-City.mmdb')


def query_city_from_geolite(ip: str) -> GeoIp2DB.Reader:
    return reader.city(ip_address=ip)
query_city_from_geolite('183.230.146.26')
# response.country.name
# response.country.names['zh-CN']
# response.city.name
# response.city.names['zh-CN']
#
# response.location.latitude
# response.location.longitude
