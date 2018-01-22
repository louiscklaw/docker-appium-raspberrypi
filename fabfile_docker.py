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


class cls_docker:
    def __init__(self):
        pass

    def init_reboot(self):
        reboot()

    @task
    def put_docker_files(self):
        print(self_configuration.text_status('creating docker workspace'))
        with settings(warn_only=True):
            sudo('mkdir /home/docker-files')
            sudo('chown pi:pi /home/docker-files')
            sudo('chmod 775 /home/docker-files')
        perform_put('docker-files/', '/home')
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
