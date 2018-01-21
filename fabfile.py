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

RUNNING_HOST = 'pi@192.168.88.180'
env.user = 'testuser'
env.hosts = [RUNNING_HOST]


CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CWD)


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
def make_wkdir(username):
    sudo('mkdir -p %s' % REMOTE_DIR)
    sudo('chown {username}:{username} {remote_dir}'.format(
        username=username,
        remote_dir=REMOTE_DIR
    ))
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
def pi_expand_disk():
    sudo('raspi-config --expand-rootfs')



@task
def docker_compose_rebuild():
    print(green('build runner'))
    with cd(REMOTE_DIR + '/docker-files/runner'):
        run('docker build . --tag logickee/raspberrypi-runner')

    with cd(REMOTE_DIR + '/docker-files'), settings(warn_only=True):
        run('docker-compose build')
        run('docker-compose up -d --scale appium_runner=6 --remove-orphans')

    # with settings(warn_only=True):
        # run('docker kill $(docker ps -q -a)')
        # run('docker rm $(docker ps -q -a)')


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


def get_current_branch():
    current_branch = local("git branch | sed -n '/\* /s///p'", capture=True)
    return current_branch


@task
def push_image():
    with cd(REMOTE_DIR + '/docker-files/runner'):
        run('docker push')


@task
def test():
    with lcd(LOCAL_DIR):
        current_branch = get_current_branch()
        local('git push')
        with cd(REMOTE_DOCKER_FILE_DIR):
            run('rm -rf %s' % PROJ_HOME)
            run('git clone %s' % git_repo_URL)

        with cd(REMOTE_DIR):
            run('git checkout -f develop')

    docker_compose_rebuild()


class self_configuration:
    text_status = green
    text_warning = yellow
    text_error = red
    TEMP_MOUNT = tempfile.TemporaryDirectory(dir='/mnt')
    RPI_IMAGE = os.path.sep.join([
        CWD, 'image/2017-11-29-raspbian-stretch-lite.img'
    ])
    sd_card_partition_name = {
        'boot':'1',
        'data':'2'
    }


    def __init__(self, dev_name):
        self.dev = dev_name

    def get_dev_partition_name(self, hahaha):
        return self.dev+self_configuration.sd_card_partition_name[hahaha]

class mounting_operation:
    def __init__(self, dev):
        self.dev = dev

    def umount_all(self):
        with settings(warn_only=True):
            for i in range(5 + 1, 0, -1):
                print(green('unmounting devices'))
                dev_string = self.dev + str(i)
                local('umount %s' % dev_string)
        return self


class cls_prepare_sd_card(
    mounting_operation, self_configuration
    ):

    def __init__(self, dev):
        self.dev = dev
        self.mounting_operation = mounting_operation(dev)

    def extract_rpi_image(self):
        cls_prepare_sd_card.text_status('extracting image')
        local('dd if=%s of=%s' % (RPI_IMAGE, self.dev))
        return self

    class mount_with_temp_dir:
        def __init__(self, dev_name):
            self.dev_name = dev_name
            self.temp_mount_dir = cls_prepare_sd_card.TEMP_MOUNT.name
            super()

        def __enter__(self):

            path_to_temp_mount = os.path.abspath(self.temp_mount_dir)

            cls_prepare_sd_card.text_status('mounting dev')
            local('mount  %s %s' % (self.dev_name, path_to_temp_mount))
            self.active_temp_mount = path_to_temp_mount

            return self.active_temp_mount

        def __exit__(self, type, value, traceback):
            if hasattr(self, 'active_temp_mount'):
                local('sync')
                local('sudo umount %s' % self.dev_name)

    def __init__(self, dev_name):
        self.dev = dev_name

    def pi_enable_ssh(self):
        """running on the assumption that the image got sdx1 and sdx2 while extracting image on the sdcard
        """
        print(self_configuration.text_status('enabling ssh'))
        with cls_prepare_sd_card(self.dev).mount_with_temp_dir(
            self.get_dev_partition_name('boot')
        ) as temp_wkdir:

            command = 'touch %s' % os.path.sep.join([
                temp_wkdir, 'ssh'
            ])
            local(command)

        return self

    def set_time_zone(self,timezone='Asia/Hong_Kong'):
        print(self_configuration.text_status('setting up timezone'))
        with cls_prepare_sd_card(self.dev).mount_with_temp_dir(
            self.get_dev_partition_name('data')
            ) as temp_wkdir:
            timezone_path = os.path.sep.join([
                temp_wkdir,'usr/share/zoneinfo', timezone])
            localtime_path = os.path.sep.join([
                temp_wkdir,'etc/localtime'
            ])

            local('rm -rf %s' % localtime_path)
            local('ln -sf %s %s' % (localtime_path, timezone_path))
        return self



    def inject_wpa_supplicant(self, SSID, PASSWORD):
        """sudo fab inject_wpa_supplicant:<SSID>,<PASSWORD>"""
        print(self_configuration.text_status('injecting wifi configuraion'))

        # wpa_passphrase "testing" "testingPassword" >> /etc/wpa_supplicant/wpa_supplicant.conf
        with cls_prepare_sd_card(self.dev).mount_with_temp_dir(
            self.get_dev_partition_name('data')
            ) as temp_wkdir:

            wpa_supplicant_path = os.path.sep.join(
                [temp_wkdir, 'etc/wpa_supplicant/wpa_supplicant.conf']
            )
            command = 'wpa_passphrase "{ssid}" "{password}" >> {wpa_file_path}'.format(
                ssid=SSID,
                password=PASSWORD,
                wpa_file_path=wpa_supplicant_path
            )
            local(command)


@task
def prepare_sd_card(dev_sd_card):
    print(cls_prepare_sd_card.text_status('preparing sdcard'))
    cls_prepare_sd_card(dev_sd_card).\
        extract_rpi_image()

@task
def init_configuration(dev_sd_card, WIFI_SSID, WIFI_PASS):

        print(cls_prepare_sd_card.text_status('post configuration'))
        cls_prepare_sd_card(dev_sd_card).\
            umount_all().\
            pi_enable_ssh().\
            set_time_zone().\
            inject_wpa_supplicant(
                WIFI_SSID, WIFI_PASS)

@task
def init_rpi_sdcard(dev_sd_card, WIFI_SSID, WIFI_PASS):
        prepare_sd_card(dev_sd_card)
        init_configuration(dev_sd_card, WIFI_SSID, WIFI_PASS)
