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


# init logging
import logging
LOGGING_FORMATTER = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
formatter = logging.Formatter(LOGGING_FORMATTER)

logging.basicConfig(
    level=logging.DEBUG,
    format=LOGGING_FORMATTER,
    datefmt='%d %m %Y %H:%M:%S',
    filename='%s' % __file__.replace('.py', '.log'),
    filemode='a')

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
# set a format which is simpler for console use

console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

# init logging


def apt_install(sw_list):
    for sw in sw_list:
        logging.info('install %s' % sw)
        sudo('apt install -y --no-install-recommends {sw}'.format(sw=sw))


@task
def install_tools():
    sudo('apt update')
    apt_install(['git', 'android-tools-adb'])


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
        sudo('useradd -u 1009 -g {username} -G users,staff,sudo -d /home/{username} -s /bin/bash -p p4$$W0R9 {username}'.format(username=username))


@task
def install_docker():
    print(green('getting docker'))
    sudo('curl -sSL https://get.docker.com | sh')
    # https://docs.docker.com/compose/install/#install-compose
    print(green('getting docker-compose'))
    sudo('apt-get -y install python-pip')
    sudo('pip install docker-compose')

    run('docker --version')
    run('docker-compose --version')

    print(green('Done', True))


@task
def docker_pull(image):
    sudo('docke')


@task
def up():
    install_tools()
    install_docker()


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
