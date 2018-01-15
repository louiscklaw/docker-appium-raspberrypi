#!/usr/bin/env python
# coding:utf-8
import os
import sys
import traceback
from pprint import pprint

from time import sleep
from fabric.api import *
from fabric.colors import *
from fabric.contrib.project import *

RUNNING_HOST = 'pi@192.168.88.180'
env.hosts = [RUNNING_HOST]

# NOTE:
# https://tinklabs.atlassian.net/wiki/spaces/ENG/pages/67829777/setup+test+environment+on+linux

PROJ_HOME = 'docker-android-emulator'
LOCAL_DIR, REMOTE_DIR = (
    '/home/logic/_workspace/docker-files/%s' % PROJ_HOME,
    '/srv/docker-files/%s' % PROJ_HOME
)

@task
def user_del(username):
    env.use_sudo = True
    run('id')

    if username not in ['']:
        sudo('userdel {username}'.format(username=username))
        sudo('groupdel {username}'.format(username=username))


@task
def user_add(username):
    env.use_sudo = True
    run('id')
    if username not in ['']:
        sudo('groupadd -g 1009 {username}'.format(username=username))
        sudo('useradd -u 1009 -g users -d /home/{username} -s /bin/bash -p p4$$W0R9 {username}'.format(username=username))


@task
def rsync():
    """rsync for use with fabric"""
    exclude_list = ['.git', '.vscode', '_ref']
    cmd_exclude_param = ' '.join(['--exclude %s' % exclude_item for exclude_item in exclude_list])

    local('rsync -rz  {cmd_exclude}  {source_dir}/ {as_user}@{running_host}:{remote_dir}'.format(
        source_dir=LOCAL_DIR,
        remote_dir=REMOTE_DIR,
        as_user=env.user,
        running_host=RUNNING_HOST,
        cmd_exclude=cmd_exclude_param
    ))
    sleep(1)
