#!/usr/bin/python3
"""
Backend for ITU project - file manager
"""

import os
from os.path import join
import subprocess
import ntpath
from pathlib import Path
import sys
import shlex
import shutil
import psutil
from datetime import datetime
from socket import gethostname
import getpass

__author__ = ["Marek Sedláček (xsedla1b)", "Klára Ungrová (xungro00)", "Ronald Telmanik (xtelma00)"]
__email__ = ["xsedla1b@fit.vutbr.cz", "xungro00@fit.vutbr.cz", "xtelma00@fit.vutbr.cz"]
__version__ = "1.0.0"


def get_divisor(metric):
    if metric == "KB":
        return 2 ** 10
    elif metric == "MB":
        return 2 ** 20
    elif metric == "GB":
        return 2 ** 30
    elif metric == "TB":
        return 2 ** 40
    else:
        return 1


class Item:

    def __init__(self, path):
        """
        :param path: Absolute path to this item
        """
        self._path = path
        self._name = ntpath.basename(path)

    def is_file(self):
        """
        :return: If object is file
        """
        return False

    def is_folder(self):
        """
        :return: If object is folder
        """
        return False

    def get_name(self):
        """
        :return: Item's name
        """
        return self._name

    def get_path(self):
        """
        :return: Item's absolute path
        """
        return self._path

    def get_parent(self):
        """
        :return: Parent folder as Folder object
        """
        return Folder(str(Path(self._path).parent))

    def rename(self, new_name):
        """
        Renames file or folder
        :param new_name: New name
        :return: None
        """
        os.rename(self.get_path(), join(self.get_parent().get_path(), new_name))
        self._path = join(self.get_parent().get_path(), new_name)
        self._name = ntpath.basename(self._path)

    def __str__(self):
        return self._path


class Folder(Item):
    """
    Folder object - represents OS directory
    Exceptions are supposed to be handled by caller
    """

    def get_content(self):
        """
        :return: list of Files and Folders (objects)
        """
        return [Folder(join(self._path, f)) if os.path.isdir(join(self._path, f)) else File(join(self._path, f)) for f in os.listdir(self._path)]

    def create_folder(self, name):
        """
        Creates new folder in this folder
        :param name: Name of the folder to be created
        :return: Folder object of the newly made folder
        """
        new_fldr = join(self.get_path(), name)
        os.mkdir(new_fldr)
        return Folder(new_fldr)

    def create_file(self, name):
        """
        Creates new file in this folder
        :param name: Name of the new file
        :raise: FileExistsError if the file already exists
        :return: File object of the newly made file
        """
        new_file = join(self.get_path(), name)
        if os.path.isfile(new_file):  # Check if file exists
            raise FileExistsError("File {} exists".format(name))
        open(new_file, 'a').close()
        return File(new_file)

    def can_be_copied(self, to):
        """
        :param to: Folder or path to which the file would be copied
        :return: If the file can be copied to the passed in destination
        """
        return not os.path.isdir(to.get_path() if type(to) == Folder else to)

    def copy(self, to, rename_duplicit=False):
        """
        Copies this file to passed in folder
        :param to: folder to which to copy (object or address)
        :return: Folder object of the copied file
        """
        new_path = join(to.get_path(), self.get_name()) if type(to) == Folder else join(to, self.get_name())
        top = to.get_path() if type(to) == Folder else to
        if rename_duplicit and not self.can_be_copied(join(top, self.get_name())):
            i = 2
            # Create unique name
            while not self.can_be_copied(join(top, self.get_name() + "(" + str(i) + ")")):
                i += 1
            new_path = join(top, self.get_name()) + "(" + str(i) + ")"

        # Remove folder if one with the same name exists
        if os.path.isdir(new_path):
            Folder(new_path).remove()
        shutil.copytree(self.get_path(), new_path)
        return Folder(new_path)

    def move(self, to, rename_duplicit=False):
        """
        Moves folder to another
        :param to: folder to which to move (object or address)
        :param rename_duplicit: renames copied file by appending number to it if
                                there already is a file with the same name
        """
        new_dest = self.copy(to, rename_duplicit)
        self.remove()
        self._path = new_dest.get_path()
        self._name = new_dest.get_name()

    def remove(self):
        """
        Removes this folder and all files and folder inside of it
        :return: Folder object of parent folder
        """
        retv = self.get_parent()
        shutil.rmtree(self.get_path())
        return retv

    def get_size(self, metric="B"):
        """
        Taken from: https://stackoverflow.com/a/1392549
        :param metric: return value metric
        :return: Folder size as float
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.get_path()):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size / get_divisor(metric)

    def get_item_count(self):
        """
        :return: How many items are in this folder
        """
        amount = 0
        for dirpath, dirnames, filenames in os.walk(self.get_path()):
            amount += len(filenames) + len(dirnames)
        return amount

    def is_folder(self):
        return True

    def __iter__(self):
        return self.get_content().__iter__()


class File(Item):
    """
    File object - represents OS file (possibly symlink)
    Exceptions are supposed to be handled by caller
    """

    def is_file(self):
        return True

    def open(self):
        """
        Opens file in default OS application
        """
        if sys.platform == "linux":
            os.system("xdg-open "+shlex.quote(self.get_path()))
        elif sys.platform == "darwin":  # Mac OS
            os.system("open "+shlex.quote(self.get_path()))
        else:
            os.system("start "+shlex.quote(self.get_path()))

    def remove(self):
        """
        Deletes file
        :return: Parent folder
        """
        retv = self.get_parent()
        os.remove(self.get_path())
        return retv

    def can_be_copied(self, to):
        """
        :param to: Folder or path to which the file would be copied
        :return: If the file can be copied to the passed in destination
        """
        return not os.path.isfile(to.get_path() if type(to) == Folder else to)

    def copy(self, to, rename_duplicit=False):
        """
        Copies this file to passed in folder
        :param to: folder to which to copy (object or address)
        :param rename_duplicit: renames copied file by appending number to it if
                                there already is a file with the same name
        """
        top = to.get_path() if type(to) == Folder else to
        if rename_duplicit and not self.can_be_copied(join(top, self.get_name())):
            i = 2
            # Create unique name
            while not self.can_be_copied(join(top, self.get_name() + "(" + str(i) + ")")):
                i += 1
            new_path = self.get_name() + "(" + str(i) + ")"
            shutil.copy(self.get_path(), join(to.get_path(), new_path) if type(to) == Folder else join(to, new_path))
            return File(join(top, new_path))
        else:
            shutil.copy(self.get_path(), to.get_path() if type(to) == Folder else to)
            return File(join(top, self.get_name()))

    def move(self, to, rename_duplicit=False):
        """
        Moves folder to another
        :param to: folder to which to move (object or address)
        :param rename_duplicit: renames copied file by appending number to it if
                                there already is a file with the same name
        """
        new_dest = self.copy(to, rename_duplicit)
        self.remove()
        self._path = new_dest.get_path()
        self._name = new_dest.get_name()

    def get_size(self, metric="B"):
        return os.path.getsize(self.get_path()) / get_divisor(metric)

    def get_modification_time(self):
        return os.path.getmtime(self.get_path())


class Disk:

    def __init__(self, info):
        self._name = info.device
        self._path = info.mountpoint

    def get_folder(self):
        return Folder(self._path)

    def get_name(self):
        return self._name

    def get_path(self):
        return self._path

    def get_free_space(self, metric="B"):
        """
        Returns free space on the disk
        :param metric: In what metric will be the value returned
                       B (Bytes) || KB (KibiBytes) || MB (MibiBytes) || GB (GibiBytes) || TB (TebiBytes)
        :return: disk capacity (float)
        """
        return shutil.disk_usage(self._path).free / get_divisor(metric)

    def get_capacity(self, metric="B"):
        """
        Returns disk capacity
        :param metric: In what metric will be the value returned
                       B (Bytes) || KB (KibiBytes) || MB (MibiBytes) || GB (GibiBytes) || TB (TebiBytes)
        :return: disk capacity (float)
        """
        return shutil.disk_usage(self._path).total / get_divisor(metric)

    def get_used_space(self, metric="B"):
        """
        Returns disk capacity
        :param metric: In what metric will be the value returned
                       B (Bytes) || KB (KibiBytes) || MB (MibiBytes) || GB (GibiBytes) || TB (TebiBytes)
        :return: disk capacity (float)
        """
        return shutil.disk_usage(self._path).used / get_divisor(metric)


class FileManager:

    def __init__(self, root_dir="/"):
        self._root = Folder(root_dir)
        self.active = Folder(root_dir)

    def get_disks(self):
        return [Disk(d) for d in psutil.disk_partitions()]

    def set_root(self, root_dir):
        self._root = Folder(root_dir)

    def get_root(self):
        return self._root

    def get_prefix(self):
        return getpass.getuser() + "@" + gethostname() + ":" + "/" + self.active.get_name() + "$"


def make_shell_command(command):
    """
    Runs a command in a subshell and returns output
    :param command: Shell command
    :return: tuple of stdout and stderr (stdout, stderr)
             If stderr is "ERROR::ITU-BACKEND: Could not run subprocess" then the subprocess could raised an exception
    """
    try:
        o = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE, env={**os.environ})
        out, err = o.communicate()
        return out.decode('utf-8') if out is not None else None, err.decode('utf-8') if err is not None else None
    except Exception:
        return None, "ERROR::ITU-BACKEND: Could not run subprocess"


if __name__ == "__main__":
    fm = FileManager()
    fm.set_root("/home/marek/Desktop/skola/ITU/test_folder")
    fldr = fm.get_root()

    print("Disks:")
    for c, a in enumerate(fm.get_disks()):
        print(str(c)+"\t"+a.get_name()+"\t: "+a.get_path()+" ("+str(round(a.get_free_space("GB"), 1))+"/"+str(round(a.get_capacity("GB"), 1))+" GB)")

    while True:
        cmdall = input("> ")
        cmd = cmdall.split()
        if cmd[0] == "ls":
            for i in fldr:
                print(i.get_name())
        elif cmd[0] == "mkdir":
            fldr.create_folder(cmd[1])
        elif cmd[0] == "cd":
            if cmd[1] == "..":
                fldr = fldr.get_parent()
            else:
                fldr = Folder(join(fldr.get_path(), cmd[1]))
        elif cmd[0] == "touch":
            fldr.create_file(cmd[1])
        elif cmd[0] == "rename" and len(cmd) == 2:
            fldr.rename(cmd[1])
        elif cmd[0] == "rename" and len(cmd) == 3:
            f = Item(join(fldr.get_path(), cmd[1]))
            f.rename(cmd[2])
        elif cmd[0] == "open":
            f = File(join(fldr.get_path(), cmd[1]))
            f.open()
        elif cmd[0] == "rm":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
            else:
                f = Folder(join(fldr.get_path(), cmd[1]))
            f.remove()
        elif cmd[0] == "cp":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
            else:
                f = Folder(join(fldr.get_path(), cmd[1]))

            if f.can_be_copied(join(join(fldr.get_path(), cmd[2]), cmd[1])):
                f.copy(join(fldr.get_path(), cmd[2]))
            else:
                print("File or Folder with the same name already exists")
        elif cmd[0] == "cp.":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
                f.copy(join(fldr.get_path(), cmd[2]), True)
            elif os.path.isdir(join(fldr.get_path(), cmd[1])):
                f = Folder(join(fldr.get_path(), cmd[1]))
                f.copy(join(fldr.get_path(), cmd[2]), True)
        elif cmd[0] == "cp!":  # Rewrites folder
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
                f.copy(join(fldr.get_path(), cmd[2]), False)
            elif os.path.isdir(join(fldr.get_path(), cmd[1])):
                f = Folder(join(fldr.get_path(), cmd[1]))
                f.copy(join(fldr.get_path(), cmd[2]), False)
        elif cmd[0] == "mv":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
            else:
                f = Folder(join(fldr.get_path(), cmd[1]))

            if f.can_be_copied(join(join(fldr.get_path(), cmd[2]), cmd[1])):
                f.move(join(fldr.get_path(), cmd[2]))
            else:
                print("File or Folder with the same name already exists")
        elif cmd[0] == "mv.":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
                f.move(join(fldr.get_path(), cmd[2]), True)
            elif os.path.isdir(join(fldr.get_path(), cmd[1])):
                f = Folder(join(fldr.get_path(), cmd[1]))
                f.move(join(fldr.get_path(), cmd[2]), True)
        elif cmd[0] == "mv!":  # Rewrites folder
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
                f.move(join(fldr.get_path(), cmd[2]), False)
            elif os.path.isdir(join(fldr.get_path(), cmd[1])):
                f = Folder(join(fldr.get_path(), cmd[1]))
                f.move(join(fldr.get_path(), cmd[2]), False)
        elif cmd[0] == "disk":
            fldr = fm.get_disks()[int(cmd[1])].get_folder()
        elif cmd[0] == "size":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
                print(str(round(f.get_size("KB"), 2))+" KB")
            elif os.path.isdir(join(fldr.get_path(), cmd[1])):
                f = Folder(join(fldr.get_path(), cmd[1]))
                print(str(round(f.get_size("KB"), 2))+" KB")
        elif cmd[0] == "time":
            if os.path.isfile(join(fldr.get_path(), cmd[1])):
                f = File(join(fldr.get_path(), cmd[1]))
                print(datetime.utcfromtimestamp(f.get_modification_time()).strftime('%Y-%m-%d %H:%M:%S'))
        elif cmd[0] == "items":
            if os.path.isdir(join(fldr.get_path(), cmd[1])):
                f = Folder(join(fldr.get_path(), cmd[1]))
                print("Contains "+str(f.get_item_count()), " items")
