#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#    Guillaume Subiron, maethor@subiron.org
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import time
from datetime import datetime, timedelta

from collections import Counter, OrderedDict
from itertools import groupby

# Will be populated by the UI with it's own value
app = None


def _graph(logs):
    groups_hour = groupby(reversed(logs), key=lambda x: (x['time'] - (x['time'] % 3600)))

    data = OrderedDict()
    for key, value in groups_hour:
        # Filling voids with zeros
        if data:
            while next(reversed(data)) < (key - 3600):
                data[next(reversed(data)) + 3600] = 0
        data[key] = len(list(value))

    # Smooth graph
    avg = sum(data.values()) / len(list(data.values()))
    variance = sum([(v - avg)**2 for v in list(data.values())]) / len(list(data.values()))
    deviation = variance**0.5

    # Remove every value that is 3 times out of standard deviation
    for key, value in list(data.items()):
        if value > (avg + deviation * 3):
            data[key] = avg

    # Remove every value that is out of standard deviation and more than two times previous value
    for key, value in list(data.items()):
        if key - 3600 in data and key + 3600 in data:
            if value > (avg + deviation) and value > (2 * data[key - 3600]):
                data[key] = (data[key - 3600] + data[key + 3600]) / 2

    if datetime.fromtimestamp(logs[-1]['time']) < (datetime.now() - timedelta(7)):
        # Group by 24h
        data_24 = OrderedDict()
        for key, value in list(data.items()):
            the_time = (key - key % (3600 * 24))
            if the_time not in data_24:
                data_24[the_time] = 0
            data_24[the_time] += value
        data = data_24

    # Convert timestamp to milliseconds
    # Convert timestamp ms to s
    graph = [{'t': k * 1000, 'y': v} for k, v in list(data.items())]

    return graph


def get_global_stats():
    user = app.get_user()
    _ = user.is_administrator() or app.redirect403()

    days = int(app.request.GET.get('days', 30))

    range_end = int(app.request.GET.get('range_end', time.time()))
    range_start = int(app.request.GET.get('range_start', range_end - (days * 86400)))

    logs = list(app.logs_module.get_ui_logs(
        range_start=range_start, range_end=range_end,
        filters={'type': 'SERVICE NOTIFICATION',
                 'command_name': {'$regex': 'notify-service-by-slack'}},
        limit=None))

    hosts = Counter()
    services = Counter()
    hostsservices = Counter()
    for log in logs:
        hosts[log['host_name']] += 1
        services[log['service_description']] += 1
        hostsservices[log['host_name'] + '/' + log['service_description']] += 1
    return {
        'hosts': hosts,
        'services': services,
        'hostsservices': hostsservices,
        'days': days,
        'graph': _graph(logs) if logs else None
    }


def get_service_stats(name):
    user = app.get_user()
    _ = user.is_administrator() or app.redirect403()

    days = int(app.request.GET.get('days', 30))

    range_end = int(app.request.GET.get('range_end', time.time()))
    range_start = int(app.request.GET.get('range_start', range_end - (days * 86400)))

    logs = list(app.logs_module.get_ui_logs(
        range_start=range_start, range_end=range_end,
        filters={'type': 'SERVICE NOTIFICATION',
                 'command_name': {'$regex': 'notify-service-by-slack'},
                 'service_description': name},
        limit=None))

    hosts = Counter()
    for log in logs:
        hosts[log['host_name']] += 1
    return {'service': name, 'hosts': hosts, 'days': days}


def get_host_stats(name):
    user = app.get_user()
    _ = user.is_administrator() or app.redirect403()

    days = int(app.request.GET.get('days', 30))

    range_end = int(app.request.GET.get('range_end', time.time()))
    range_start = int(app.request.GET.get('range_start', range_end - (days * 86400)))

    logs = list(app.logs_module.get_ui_logs(
        range_start=range_start, range_end=range_end,
        filters={'type': 'SERVICE NOTIFICATION',
                 'command_name': {'$regex': 'notify-service-by-slack'},
                 'host_name': name},
        limit=None))

    services = Counter()
    for log in logs:
        services[log['service_description']] += 1
    return {'host': name, 'services': services, 'days': days}


pages = {
    get_global_stats: {
        'name': 'GlobalStats', 'route': '/stats', 'view': 'stats'
    },

    get_service_stats: {
        'name': 'Stats', 'route': '/stats/service/<name:path>', 'view': 'stats_service'
    },

    get_host_stats: {
        'name': 'Stats', 'route': '/stats/host/<name:path>', 'view': 'stats_host'
    }
}
