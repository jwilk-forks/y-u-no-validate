# Copyright © 2014-2016 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import contextlib
import datetime
import os
import re
import shutil
import subprocess as ipc
import tempfile
import xml.etree.ElementTree as et

class Firefox(object):

    def __init__(self, url):
        self.url = url
        self.child = None
        version = ipc.check_output(['firefox', '--version'])
        version = version.decode('ASCII')
        version = re.search(r'(\d+)', version).group(0)
        self.version = int(version)

    def __enter__(self):
        with open(os.devnull, 'wb') as dev_null:
            self.child = ipc.Popen(
                ['firefox', '-no-remote', self.url],
                stderr=dev_null,
            )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.child.terminate()
        self.child.wait()

    def wait(self):
        self.child.wait()

    def get_window_id(self, window_name):
        cmdline = [
            'xdotool',
            'search',
                '--sync',
                '--limit', '1',
                '--all',
                '--pid', str(self.child.pid),
                '--name', window_name,
        ]
        output = ipc.check_output(cmdline)
        return int(output)

    def activate_window(self, window):
        cmdline = ['xdotool']
        if isinstance(window, int):
            cmdline += [
                'windowactivate', '--sync', str(window)
            ]
        else:
            cmdline += [
                'search',
                    '--sync',
                    '--limit', '1',
                    '--all',
                    '--pid', str(self.child.pid),
                    '--name', window,
                'windowactivate', '--sync',
            ]
        ipc.check_call(cmdline)

    def talk(self, window, *args):
        self.activate_window(window)
        cmdline = ['xdotool', 'key']
        for arg in args:
            if arg[:1] + arg[-1:] == '<>':
                for ch in arg[1:-1]:
                    if ch == ' ':
                        cmdline += ['space']
                    else:
                        cmdline += [ch]
            else:
                cmdline += [arg]
        ipc.check_call(cmdline)

profiles_ini = '''\
[General]
StartWithLastProfile=1

[Profile0]
Name=default
IsRelative=1
Path=default
'''

xml_namespaces = dict(
    em='http://www.mozilla.org/2004/em-rdf#'
)

def get_addon_id():
    rdf_path = os.path.dirname(__file__) + '/../src/install.rdf'
    with open(rdf_path, 'rb') as rdf_file:
        rdf_tree = et.parse(rdf_file)
        id_elem = rdf_tree.find('.//em:id', namespaces=xml_namespaces)
        return id_elem.text

prefs_js = '''
user_pref("network.proxy.http", "127.0.0.1");
user_pref("network.proxy.http_port", 9);
user_pref("network.proxy.ssl", "127.0.0.1");
user_pref("network.proxy.ssl_port", 9);
user_pref("network.proxy.type", 1);
user_pref("extensions.enabledItems", "{addon_id}:{today}");
'''.format(addon_id=get_addon_id(), today=datetime.date.today())

@contextlib.contextmanager
def clean_home_dir():
    home = tempfile.mkdtemp(prefix='y-u-no-validate.')
    try:
        mozilla_home = home + '/.mozilla/firefox'
        os.makedirs(mozilla_home + '/default')
        with open(mozilla_home + '/profiles.ini', 'wt', encoding='ASCII') as file:
            file.write(profiles_ini)
        with open(mozilla_home + '/default/prefs.js', 'wt', encoding='ASCII') as file:
            file.write(prefs_js)
        old_home = os.environ['HOME']
        os.environ['HOME'] = home
        try:
            yield
        finally:
            os.environ['HOME'] = old_home
    finally:
        shutil.rmtree(home)

# vim:ts=4 sts=4 sw=4 et
