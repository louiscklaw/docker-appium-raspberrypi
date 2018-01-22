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


def get_current_branch():
    current_branch = local("git branch | sed -n '/\* /s///p'", capture=True)
    return current_branch


def git_push_remote_pull():
    # TODO: 🤦 update me
    # with lcd(LOCAL_DIR):
    #     current_branch = get_current_branch()
    #     local('git push')
    #     with cd(REMOTE_DOCKER_FILE_DIR):
    #         run('rm -rf %s' % PROJ_HOME)
    #         run('git clone %s' % git_repo_URL)

    #     with cd(REMOTE_DIR):
    #         run('git checkout -f develop')

    # docker_compose_rebuild()
    pass
