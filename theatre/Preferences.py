#!/usr/bin/env python3

import os, platform
from configparser import ConfigParser

CONFIGFILE = 'config.ini' # configuration file name

def is_windows():

    """
    Returns True if program runs in Windows.

    """
    return platform.uname().system == 'Windows'

def singleton(cls):

    """
    Restricts the instantiation of a class to one object.

    """
    instances = {}
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance

@singleton
class Preferences:

    """
    Program preferences manager. To access
    options use following syntax:

    Preferences()[SECTION][OPTION]

    SECTION - name of the section
    OPTION - name of the option

    """
    # default settings used if there is no configuration file
    # or its content is broken
    DEFAULTS = {'SYNC': {'sync_interval': 3600}}

    def __init__(self):
        userdir = os.path.expanduser('~') # get user home directory
        if is_windows():
            # in Windows use simple directory name
            self.homedir = os.sep.join([userdir, 'theatre'])
        else:
            # in *nix systems use directory name that starts
            # with a dot character to make it hidden
            self.homedir = os.sep.join([userdir, '.theatre'])
        if not os.path.isdir(self.homedir):
            # create directory if it does not exist
            os.mkdir(self.homedir)
            if is_windows():
                # make directory hidden in Windows
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.homedir, 0x02)
        self.config = ConfigParser() # create parser of INI files
        self.section = None # current section name
        try:
            # try to read and parse the config file
            with open(self.at_home(CONFIGFILE), 'r') as configfile:
                self.config.read_file(configfile)
            # check existance of all options in all sections
            # in the config file
            for section, options in self.DEFAULTS.items():
                for option in options:
                    # if an option not found in the config file
                    if not option in self.config[section]:
                        # the config file is broken
                        raise KeyError
        except:
            # if config file does not exist
            # or it is broken
            self.config.clear() # remove all loaded options
            # and fill configuration with default values
            for key, value in self.DEFAULTS.items():
                self.config[key] = value
            self.save() # save defaul settings in the file

    def __getitem__(self, key):

        """
        At first call changes current section
        and returns self.

        At second call returns a value of requested
        option and resets current section.

        """
        if self.section is None: # if it's first call
            self.section = key # change current section
            return self
        # second call
        section = self.section # save current section name
        self.section = None # reset current section
        # return an option value, convert a type of the value
        # to type of such default value (all settings in config file have str type)
        return type(self.DEFAULTS[section][key])(self.config[section][key])

    def __setitem__(self, key, value):

        """
        Sets values of options.

        """
        # don't create new options, use existing only
        if not key in self.config[self.section]:
            raise KeyError
        self.config[self.section][key] = str(value)
        self.section = None # reset current section

    def save(self):

        """
        Saves settings to the file.

        """
        with open(self.at_home(CONFIGFILE), 'w') as configfile:
            self.config.write(configfile)

    def at_home(self, filename):

        """
        Adds a path to the home directory to the filename.

        """
        return os.sep.join([self.homedir, filename])



if __name__ == '__main__':

    prefs = Preferences()
    prefs['SYNC']['sync_interval'] = 4200
    print(prefs['SYNC']['sync_interval'])
    prefs.save()
