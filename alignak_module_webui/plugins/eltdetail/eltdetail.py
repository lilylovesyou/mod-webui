#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


# Specific logger configuration
import logging
from alignak.log import ALIGNAK_LOGGER_NAME
logger = logging.getLogger(ALIGNAK_LOGGER_NAME + ".webui")


# Will be populated by the UI with it's own value
app = None


# Host element view
def show_host(host_name):
    # Ok, we can lookup it
    user = app.get_user()

    host = app.datamgr.get_host(host_name, user) or app.redirect404()
    logger.debug("Show host: %s", host)

    # Set hostgroups level ...
    app.datamgr.set_hostgroups_level(user)

    # Get graph data. By default, show last 4 hours
    now = int(time.time())
    graphstart = int(app.request.GET.get('graphstart', str(now - 4 * 3600)))
    graphend = int(app.request.GET.get('graphend', str(now)))

    return {
        'elt': host,
        'graphstart': graphstart, 'graphend': graphend,
        'configintervallength': app.datamgr.get_configuration_parameter('interval_length')
    }


# Service element view
def show_service(host_name, service):
    user = app.get_user()

    service = app.datamgr.get_service(host_name, service, user) or app.redirect404()
    logger.debug("Show service: %s", service)

    # Set servicegroups level ...
    app.datamgr.set_servicegroups_level(user)

    # Get graph data. By default, show last 4 hours
    now = int(time.time())
    graphstart = int(app.request.GET.get('graphstart', str(now - 4 * 3600)))
    graphend = int(app.request.GET.get('graphend', str(now)))

    return {
        'elt': service,
        'graphstart': graphstart, 'graphend': graphend,
        'configintervallength': app.datamgr.get_configuration_parameter('interval_length')
    }


pages = {
    show_host: {
        'name': 'Host', 'route': '/host/:host_name', 'view': 'eltdetail',
        'static': True
    },
    show_service: {
        'name': 'Service', 'route': '/service/:host_name/:service#.+#', 'view': 'eltdetail',
        'static': True
    }
}
