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
env.user = 'testuser'
env.hosts = [RUNNING_HOST]

# NOTE:
# https://tinklabs.atlassian.net/wiki/spaces/ENG/pages/67829777/setup+test+environment+on+linux

PROJ_HOME = 'docker-appium-raspberrypi'
LOCAL_DIR, REMOTE_DIR = (
    '/home/logic/_workspace/docker-files/' + PROJ_HOME,
    '/home/testuser/' + PROJ_HOME
)


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


def command_feeder(command):
    sudo(command)


def apt_install(sw_list):
    for sw in sw_list:
        logging.info('install %s' % sw)
        command_feeder('apt install -y --no-install-recommends {sw}'.format(sw=sw))


def pip_install(pip_list):
    for pip_wanted in pip_list:
        logging.info('install %s' % pip_wanted)
        command_feeder('pip3 install {pip_wanted}'.format(pip_wanted=pip_wanted))


def apt_recipe():
    sudo('apt update')
    apt_install([
        'git',
        'android-tools-adb',
        'tmux',
        'python3',
        'python3-pip',
        'unzip', 'rsync',
        'htop', 'glances'
    ])
    sudo('apt clean')

    # apt_verify([
    #     'python3 --version',
    #     'pip3 --version',
    #     'tmux -V',
    #     'adb version',
    #     'fastboot --version',
    #     'git --version'

    # ])


@task
def pip_recipe():
    pip_install([
        'pipenv'
    ])

    # pip_verify(
    #     ['pipenv --version']
    # )


@task
def install_tools():
    with hide('output'):
        apt_recipe()
        pip_recipe()


@task
def user_del(username):
    user_home_dir = '/home/' + username
    env.use_sudo = True
    run('id')

    if username not in ['']:
        with settings(warn_only=True):
            sudo('userdel {username}'.format(username=username))
            sudo('groupdel {username}'.format(username=username))
            sudo('rm -rf %s' % user_home_dir)


@task
def user_add(username):
    user_home_dir = '/home/' + username
    env.use_sudo = True
    run('id')

    if username not in ['']:
        sudo('groupadd -g 1009 {username}'.format(username=username))
        sudo('useradd -u 1009 -g {username} -G users,staff,sudo -d /home/{username} -s /bin/bash -p p4$$W0R9 {username}'.format(username=username))
        sudo('mkdir %s' % user_home_dir)
        sudo('chmod 775 %s' % user_home_dir)
        sudo('chown {username}:{username} {user_home_dir}'.format(
            username=username,
            user_home_dir=user_home_dir
        ))


@task
def install_docker(list_of_users_tobein_docker_group=['pi']):
    print(green('getting docker'))
    sudo('curl -sSL https://get.docker.com | sh')
    # https://docs.docker.com/compose/install/#install-compose
    print(green('getting docker-compose'))
    sudo('apt-get -y install python-pip')
    sudo('pip install docker-compose')

    run('docker --version')
    run('docker-compose --version')

    print(green('putting pi into docker group'))
    for user in list_of_users_tobein_docker_group:
        sudo('usermod -aG docker %s' % user)

    print(green('Done', True))


@task
def put_docker_files():
    with settings(warn_only=True):
        sudo('mkdir /home/docker-files')
        sudo('chown pi:pi /home/docker-files')
        sudo('chmod 775 /home/docker-files')
    rsync('docker-files/', '/home/docker-files')


@task
def docker_pull(image):
    sudo('docker')


@task
def up():
    install_tools()
    install_docker()


@task
def rsync(input_local_dir=LOCAL_DIR, input_remote_dir=REMOTE_DIR):
    """rsync for use with fabric"""

    exclude_list = ['.git', '.vscode', '_ref']
    cmd_exclude_param = ' '.join(['--exclude %s' % exclude_item for exclude_item in exclude_list])

    rsync_project(
        local_dir=input_local_dir + '/',
        remote_dir=input_remote_dir,
        exclude=exclude_list,
        delete=True
    )

    sleep(1)


@task
def make_wkdir(username):
    sudo('mkdir -p %s' % REMOTE_DIR)
    sudo('chown {username}:{username} {remote_dir}'.format(
        username=username,
        remote_dir=REMOTE_DIR
    ))


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
    with cd(DOCKER_FILE_DIR + '/runner'):
        run('docker build .')

    with cd(DOCKER_FILE_DIR):
        run('docker-compose build')
