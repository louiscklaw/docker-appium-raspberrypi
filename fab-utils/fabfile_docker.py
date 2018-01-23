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
from fabfile_common import *


class cls_docker:
    def __init__(self):
        pass

    def init_reboot(self):
        reboot()

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

    def put_docker_files(self):
        print(self_configuration.text_status('creating docker workspace'))
        with settings(warn_only=True):
            sudo('mkdir /home/docker-files')
            sudo('chown pi:pi /home/docker-files')
            sudo('chmod 775 /home/docker-files')
        put(LOCAL_DOCKER_FILE_DIR, '/home')
        return self

    def install_docker(self, list_of_users_tobein_docker_group=['pi']):
        print(self_configuration.text_status('install docker'))
        sudo('curl -sSL https://get.docker.com | sh')
        # https://docs.docker.com/compose/install/#install-compose
        print(self_configuration.text_status('getting docker-compose'))
        sudo('apt-get -y install python python-pip')
        sudo('pip3 install docker-compose')

        run('docker --version')
        run('docker-compose --version')

        print(self_configuration.text_status('putting pi into docker group'))
        for user in list_of_users_tobein_docker_group:
            sudo('usermod -aG docker %s' % user)

        print(self_configuration.text_status('Done', True))
        return self

    def docker_compose_rebuild(self):
        print(self_configuration.text_status('build runner'))
        # with cd(REMOTE_DOCKER_FILE_DIR + '/runner'):
        #     run('docker build . --tag logickee/raspberrypi-runner')

        with cd(REMOTE_DOCKER_FILE_DIR), settings(warn_only=True):
            run('docker-compose pull')
            run('docker-compose up -d --scale appium_runner=6 --remove-orphans')
        return self
