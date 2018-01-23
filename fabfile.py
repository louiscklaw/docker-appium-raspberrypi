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


@task
def clear_wkdir():
    sudo('rm -rf %s' % REMOTE_DIR)


@task
def inject_wpa_supplicant(SSID, PASSWORD):
    """sudo fab inject_wpa_supplicant:<SSID>,<PASSWORD>"""

    # wpa_passphrase "testing" "testingPassword" >> /etc/wpa_supplicant/wpa_supplicant.conf
    WK_DIR = '/mnt/2'
    wpa_supplicant_path = os.path.sep.join(
        [WK_DIR, 'etc/wpa_supplicant/wpa_supplicant.conf']
    )
    command = 'wpa_passphrase "{ssid}" "{password}" >> {wpa_file_path}'.format(
        ssid=SSID,
        password=PASSWORD,
        wpa_file_path=wpa_supplicant_path
    )

    wpa_supplicant_dir = os.path.dirname(wpa_supplicant_path)

    with cd(wpa_supplicant_path):
        local(command)


@task
def pi_enable_ssh():
    WK_DIR = '/mnt/1'
    command = 'touch /mnt/1/ssh'
    with cd(WK_DIR):
        local(command)


@task
def pi_expand_disk():
    sudo('raspi-config --expand-rootfs')


@task
def set_time_zone(timezone='Asia/Hong_Kong'):
    print(green('setting up timezone'))
    string_timezone = os.path.sep.join(['/usr/share/zoneinfo', timezone])
    sudo('rm -rf /etc/localtime')
    sudo('ln -sf %s /etc/localtime' % string_timezone)
    sudo('service syslog restart')
    sudo('date')


@task
def docker_compose_rebuild():
    DOCKER_FILE_DIR = '/home/docker-files'
    rsync('docker-files/', DOCKER_FILE_DIR)
    print(green('build runner'))

    with settings(warn_only=True):
        run('docker kill $(docker ps -q -a)')
        run('docker rm $(docker ps -q -a)')

    with cd(DOCKER_FILE_DIR + '/runner'):
        run('docker build . --tag logickee/raspberrypi-runner')

    with cd(DOCKER_FILE_DIR):
        run('docker-compose build')
        run('docker-compose up -d --scale appium_runner=4 --remove-orphans')


@task
def slim_down_raspberry():
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep x11 | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep sound | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep gnome | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep lxde | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep gtk | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep desktop | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep gstreamer | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep avahi | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep dbus | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep freetype | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep penguinspuzzle | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep xkb-data | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep xdg | sed s/install//`')
    sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "deinstall" | grep shared-mime-info | sed s/install//`')
    sudo('apt-get -y autoremove')


@task
def up():
    slim_down_raspberry()
    install_tools()
    install_docker()


def cook_slimdown():
    """trim down the image for docker on rpi"""
    rpi_init().\
        slim_down_raspberry().\
        user_add('logic')


@task
def cook_docker_container():
    """download container image and build it on pi"""
    cls_docker().\
        put_docker_files().\
        docker_compose_rebuild()


@task
def cook_add_user():
    rpi_init().\
        user_del('test_user').\
        user_add('test_user', 'test_user').\
        enable_empty_password('test_user')


@task
def build_docker_image():
    with cd(REMOTE_DOCKER_FILE_DIR):
        run('docker build --tag logickee/raspberrypi-runner runner/.')
