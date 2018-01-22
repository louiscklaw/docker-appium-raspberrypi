#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import traceback
from pprint import pprint

import tempfile

from time import sleep
from fabric.api import *
from fabric.colors import *
from fabric.contrib.project import *
from fabric.contrib.files import *
from fabric.operations import *

from fabfile_rpi import *
from fabfile_docker import *
from fabfile_git import *

RUNNING_HOST = 'pi@192.168.88.180'
env.user = 'testuser'
env.hosts = [RUNNING_HOST]


CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CWD)


# NOTE: ㊙ ️FILES for cooking the sdcard
SSH_PUB_KEY_FILE = os.path.sep.join([
    CWD, '_files', 'ssh_key', 'id_rsa.pub'
])
RPI_AUTH_KEY_FILENAME = 'authorized_keys'
DOT_SSH_PATH = 'home/pi/.ssh'


# NOTE:
# https://tinklabs.atlassian.net/wiki/spaces/ENG/pages/67829777/setup+test+environment+on+linux

PROJ_HOME = 'docker-appium-raspberrypi'
REMOTE_DOCKER_FILE_DIR = '/home/docker-files'

LOCAL_DIR, REMOTE_DIR = (
    '/home/logic/_workspace/docker-files/' + PROJ_HOME,
    REMOTE_DOCKER_FILE_DIR + '/' + PROJ_HOME
)

git_repo_URL = 'https://github.com/louiscklaw/docker-appium-raspberrypi.git'

env.user = 'pi'
env.password = 'raspberry'

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


def git_push_remote_pull():
    with lcd(LOCAL_DIR):
        current_branch = get_current_branch()
        local('git push')
        with cd(REMOTE_DOCKER_FILE_DIR):
            run('rm -rf %s' % PROJ_HOME)
            run('git clone %s' % git_repo_URL)

        with cd(REMOTE_DIR):
            run('git checkout -f develop')

    docker_compose_rebuild()


def perform_put(input_local_dir=LOCAL_DIR, input_remote_dir=REMOTE_DIR):
    """rsync for use with fabric"""

    exclude_list = ['.git', '.vscode', '_ref']
    cmd_exclude_param = ' '.join(['--exclude %s' % exclude_item for exclude_item in exclude_list])

    # rsync_project(
    #     local_dir=input_local_dir ,
    #     remote_dir=input_remote_dir,
    #     exclude=exclude_list,
    #     delete=True
    # )
    put(input_local_dir, input_remote_dir)

    sleep(1)


def push_image():
    with cd(REMOTE_DIR + '/docker-files/runner'):
        run('docker push')


def prepare_sd_card(dev_sd_card):
    print(cls_prepare_sd_card.text_status('preparing sdcard'))
    cls_prepare_sd_card(dev_sd_card).\
        extract_rpi_image()


def init_configuration(dev_sd_card, WIFI_SSID, WIFI_PASS):
    print(cls_prepare_sd_card.text_status('post configuration'))
    cls_prepare_sd_card(dev_sd_card).\
        umount_all().\
        pi_enable_ssh().\
        set_time_zone().\
        inject_wpa_supplicant(
            WIFI_SSID, WIFI_PASS).\
        import_ssh_key().\
        umount_all()


@task
def cook_rpi_sdcard(dev_sd_card, WIFI_SSID, WIFI_PASS):
    """initialize the sdcard for pi"""
    prepare_sd_card(dev_sd_card)
    init_configuration(dev_sd_card, WIFI_SSID, WIFI_PASS)


@task
def cook_rpi_node():
    """to init the rpi after sdcard inserted"""
    # pi_expand_disk().\

    rpi_init().\
        install_tools()


@task
def cook_docker_compose():
    """install docker and docker-compose on rpi"""
    cls_docker().\
        install_docker()


@task
def cook_slimdown():
    """trim down the image for docker on rpi"""
    rpi_init().\
        slim_down_raspberry()


@task
def cook_docker_container():
    """download container image and build it on pi"""
    cls_docker().\
        put_docker_files().\
        docker_compose_rebuild()
