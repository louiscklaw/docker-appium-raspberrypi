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

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CWD)


# NOTE:
# https://tinklabs.atlassian.net/wiki/spaces/ENG/pages/67829777/setup+test+environment+on+linux

PROJ_HOME = 'docker-appium-raspberrypi'
LOCAL_DOCKER_FILE_DIR = os.path.sep.join([
    CWD, '..', 'docker-files'
])
REMOTE_DOCKER_FILE_DIR = '/home/docker-files'

LOCAL_DIR, REMOTE_DIR = (
    '/home/logic/_workspace/docker-files/' + PROJ_HOME,
    REMOTE_DOCKER_FILE_DIR + '/' + PROJ_HOME
)


class self_configuration:
    text_status = green
    text_warning = yellow
    text_error = red

    TEMP_MOUNT = tempfile.TemporaryDirectory(dir='/home/logic/_temp')
    RPI_IMAGE = os.path.sep.join([
        CWD, '..', '_files', 'image/2017-11-29-raspbian-stretch-lite.img'
    ])

    sd_card_partition_name = {
        'boot': '1',
        'data': '2'
    }

    def __init__(self, dev_name):
        self.dev = dev_name

    def get_dev_partition_name(self, hahaha):
        return self.dev + self_configuration.sd_card_partition_name[hahaha]
