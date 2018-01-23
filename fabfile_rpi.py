#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import traceback
from pprint import pprint

import tempfile

from crypt import crypt

from time import sleep
from fabric.api import *
from fabric.colors import *
from fabric.contrib.project import *
from fabric.contrib.files import *
from fabric.operations import *


CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CWD)


class self_configuration:
    text_status = green
    text_warning = yellow
    text_error = red

    TEMP_MOUNT = tempfile.TemporaryDirectory(dir='/home/logic/_temp')
    RPI_IMAGE = os.path.sep.join([
        CWD, '_files', 'image/2017-11-29-raspbian-stretch-lite.img'
    ])

    sd_card_partition_name = {
        'boot': '1',
        'data': '2'
    }

    def __init__(self, dev_name):
        self.dev = dev_name

    def get_dev_partition_name(self, hahaha):
        return self.dev + self_configuration.sd_card_partition_name[hahaha]


class mounting_operation:
    def __init__(self, dev):
        self.dev = dev

    def unmount_dev(self, test):
        # TODO: 🤦 retry unmount on busy
        pass

    def umount_all(self):
        local('sync')
        sleep(5)
        with settings(warn_only=True), hide('output', 'stderr', 'stdout'):
            for i in range(5 + 1, 0, -1):
                print(green('unmounting devices'))
                dev_string = self.dev + str(i)
                result = local('umount %s' % dev_string, capture=True)
        return self


class rpi_init:
    def __init__(self):
        pass

    # def make_wkdir(username):
    #     sudo('mkdir -p %s' % REMOTE_DIR)
    #     sudo('chown {username}:{username} {remote_dir}'.format(
    #         username=username,
    #         remote_dir=REMOTE_DIR
    #     ))
    #     local('rsync -rz  {cmd_exclude}  {source_dir}/ {as_user}@{running_host}:{remote_dir}'.format(
    #         source_dir=LOCAL_DIR,
    #         remote_dir=REMOTE_DIR,
    #         as_user=env.user,
    #         running_host=RUNNING_HOST,
    #         cmd_exclude=cmd_exclude_param
    #     ))
    #     sleep(1)

    # def clear_wkdir():
    #     sudo('rm -rf %s' % REMOTE_DIR)

    def pi_expand_disk(self):
        run('raspi-config --expand-rootfs')
        return self

    def apt_install(self, sw_list):
        for sw in sw_list:
            print(self_configuration.text_status('install %s' % sw))
            sudo('apt install -y --no-install-recommends {sw}'.format(sw=sw))

    def apt_recipe(self):
        sudo('apt update')
        self.apt_install([
            'git',
            'android-tools-adb', 'android-tools-fastboot',
            'tmux',
            'python3', 'python3-pip',
            'python', 'python-pip',
            'unzip', 'rsync',
            'htop', 'glances'
        ])
        sudo('apt clean')

    def global_pip_install(self, pip_list):
        for pip_wanted in pip_list:
            print(self_configuration.text_status('install %s' % pip_wanted))
            sudo('pip3 install {pip_wanted}'.format(pip_wanted=pip_wanted))

    def pip_recipe(self):
        self.global_pip_install([
            'pipenv'
        ])

    def install_tools(self):
        with hide('output'):
            self.apt_recipe()
            self.pip_recipe()
        return self

    def slim_down_raspberry(self):
        sw_to_remove = ["avahid",
                        "dbusd",
                        "desktopd",
                        "freetyped",
                        "gnomed",
                        "gstreamerd",
                        "gtkd",
                        "lxded",
                        "penguinspuzzled",
                        "shared-mime-infod",
                        "soundd",
                        "x11d",
                        "xdgd",
                        "xkb-datad"]

        with settings(warn_only=True), hide('stdout', 'stderr'):
            for sw in sw_to_remove:
                sudo('apt-get -y remove `sudo dpkg --get-selections | grep -v "{sw}" | grep x11 | sed s/install//`'.format(
                    sw=sw
                ))

            sudo('apt-get -y autoremove')
        return self

    def change_pi_password(self):
        password = '123321'
        user = 'pi'

        crypted_password = crypt(password, 'salt')
        sudo('usermod --password %s %s' % (crypted_password, user), pty=False)
        return self

    def user_del(self, username):
        user_home_dir = '/home/' + username
        env.use_sudo = True
        run('id')

        if username not in ['']:
            with settings(warn_only=True):
                sudo('userdel {username}'.format(username=username))
                sudo('groupdel {username}'.format(username=username))
                sudo('rm -rf %s' % user_home_dir)

        return self

    def user_add(self, username, password):
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
            sudo('echo -e "{password}\n{password}" | passwd {username}'.format(
                username=username,
                password=password
            ))
        return self

    def install_my_dotfiles(self):
        """ Copies down my dotfiles repository from GitHub.
        Installs only those files which might be relevant to the Raspberry Pi.
        See http://github.com/moopet/dotfiles
        """
        puts(green("Installing dotfiles"))
        dotfiles = (
            ".vimrc",
            ".ackrc",
            ".htoprc",
            ".gitignore",
            ".gitconfig",
            ".fonts",  # patched font for vim-powerline
            ".tmux.conf",
        )
        with hide("output", "running"), cd("/tmp"):
            if dir_exists("dotfiles"):
                with cd("dotfiles"):
                    run("git pull")
            else:
                run("git clone git://github.com/moopet/dotfiles.git")
            for f in dotfiles:
                puts("{i} {f}".format(i=INDENT, f=f))
                run("cp -r dotfiles/{} ~/".format(f))

        return self

    def enable_empty_password(self, username):
        sudo('echo "{username} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/099_{username}-nopasswd'.format(username=username))
        return self


class cls_prepare_sd_card(mounting_operation, self_configuration):

    def __init__(self, dev):
        self.dev = dev
        self.mounting_operation = mounting_operation(dev)

    def extract_rpi_image(self):
        cls_prepare_sd_card.text_status('extracting image')
        local('dd if=%s of=%s' % (self_configuration.RPI_IMAGE, self.dev))
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
                sleep(3)
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

    def set_time_zone(self, timezone='Asia/Hong_Kong'):
        print(self_configuration.text_status('setting up timezone'))
        with cls_prepare_sd_card(self.dev).mount_with_temp_dir(
            self.get_dev_partition_name('data')
        ) as temp_wkdir:
            timezone_path = os.path.sep.join([
                temp_wkdir, 'usr/share/zoneinfo', timezone])
            localtime_path = os.path.sep.join([
                temp_wkdir, 'etc/localtime'
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

        return self

    def import_ssh_key(self):
        print(self_configuration.text_status('importing pub key'))
        with cls_prepare_sd_card(self.dev).mount_with_temp_dir(
            self.get_dev_partition_name('data')
        ) as temp_wkdir:

            RPI_DOT_SSH_PATH = os.path.sep.join([
                temp_wkdir, DOT_SSH_PATH
            ])
            AUTH_PUB_KEY_PATH = os.path.sep.join([
                RPI_DOT_SSH_PATH, RPI_AUTH_KEY_FILENAME
            ])

            local('mkdir -p %s' % os.path.dirname(os.path.abspath(
                AUTH_PUB_KEY_PATH
            )))
            local('cp %s %s' % (SSH_PUB_KEY_FILE, AUTH_PUB_KEY_PATH))

        return self
