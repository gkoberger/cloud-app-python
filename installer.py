import httplib
import json
import os
import re
import shutil
from subprocess import Popen, PIPE
import sys
import urllib
import urllib2

IGNORE_PATTERNS = ('CVS','.git')

class Compiler:
    settings = []
    folder = ''
    subdomain = ''
    whitelist = ['css', 'less',
                 'html', 'htm',
                 'js', 'coffee', 'json',
                 'jpg', 'png', 'jpeg', 'gif', 'webp']
    logs = []

    def check_files(self, path):
        move = [] # List of tuples to be moved at the end

        for path_child in os.listdir(path):
            full_path = '%s/%s' % (path, path_child)
            if(path_child == ".git"):
              pass
            elif(path_child.startswith(".")):
              self.log(2, "Removing %s" % path_child, "Hidden files aren't supported")
              if(os.path.isdir(full_path)):
                  shutil.rmtree(full_path)
              else:
                  os.remove(full_path)
            elif(os.path.isdir(full_path)):
                self.check_files(full_path)
            else:
                suffix = path_child.split('.')[-1]
                if suffix not in self.whitelist:
                    self.log(2, "Removing %s" % path_child, "The filetype isn't supported")
                    os.remove(full_path)

                current_path = full_path
                if self.settings['preprocess'] == "1":
                    if full_path.endswith('less'):
                        #shutil.copyfile(full_path, '%s.old' % full_path)
                        current_path = '%s.css' % full_path

                        p = Popen(['lessc', full_path, current_path], stdout=PIPE)
                        p.communicate()

                        move.append((current_path, full_path))

                    if full_path.endswith('coffee'):
                        old_coffee = '%s/_old_%s' % (path, path_child)
                        old_js = re.sub(r'\.coffee$', '.js', old_coffee)
                        shutil.copyfile(full_path, old_coffee)

                        p = Popen(['coffee', '-c', old_coffee], stdout=PIPE)
                        p.communicate()

                        os.remove(old_coffee)
                        shutil.move(old_js, full_path)

                if self.settings['minify'] == "1":
                    if full_path.endswith('js') or full_path.endswith('coffee'):
                        p = Popen(['uglifyjs', '--overwrite', full_path], stdout=PIPE)
                        p.communicate()

                    if current_path.endswith('css'):
                        new_path = '%s.min' % current_path

                        p = Popen(['lessc', '-x', current_path, new_path], stdout=PIPE)
                        p.communicate()

                        os.remove(current_path)
                        shutil.move(new_path, current_path)

        # We do this because of less imports
        for (m_from, m_to) in move:
            if os.path.exists(m_to):
                os.remove(m_to)
            shutil.move(m_from, m_to)

    def create_manifest(self):
        manifest = {
                'name': self.settings['repo_name'],
                'description': self.settings['description'],
                'icons': {
                    '16': 'http://%s.appcloudy.com/icon-16.png' % self.subdomain,
                    '48': 'http://%s.appcloudy.com/icon-48.png' % self.subdomain,
                    '128': 'http://%s.appcloudy.com/icon-128.png' % self.subdomain,
                    }
                }

        json.dump(manifest, open('%s/manifest.webapp' % self.folder, 'w'))

    def log(self, severity, error, more=""):
        # Errors:
        # - 0: Fatal
        # - 1: Error
        # - 2: Warning
        # - 3: Info
        self.logs.append(dict(severity=severity, error=error, more=more))

    def post(self, url, data_dict):
        data = urllib.urlencode(data_dict)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()

        #import pdb; pdb.set_trace()

        return;

        params = urllib.urlencode(data)
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        conn = httplib.HTTPConnection("appcloudy.com")
        conn.request("POST", url, params, headers)
        response = conn.getresponse()
        conn.close()

    def __init__(self, folder, subdomain, job_id):
        self.subdomain = subdomain
        self.folder = folder
        self.settings = []

        req = urllib2.Request("http://appcloudy.com/getjob/%s_%s/" % (subdomain, job_id))
        opener = urllib2.build_opener()
        f = opener.open(req)

        self.settings = json.load(f)

        if(self.settings['job_found']):
            folder_build = '../build_area/%s' % subdomain
            if os.path.exists(folder_build):
                shutil.rmtree(folder_build)

            # Check out project
            p = Popen(['git', 'clone', self.settings['git_url'], folder_build], stdout=PIPE)
            p.communicate()

            # Get HEAD
            p = Popen(['git', 'rev-parse', '--short', 'HEAD'], stdout=PIPE)
            head_tuple = p.communicate()
            head = head_tuple[0].strip()

            # Check all the files
            errors = self.check_files(folder_build)

            # Copy over whole thing
            if os.path.exists(folder):
                shutil.rmtree(folder)
            shutil.copytree(folder_build, folder, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))

            # Copy over htaccess file
            shutil.copyfile('base_files/htaccess', '%s/.htaccess' % folder)

            # Create manifest
            self.create_manifest()

        # Save logs
        if not os.path.exists('logs/%s' % subdomain):
            os.makedirs('logs/%s' % subdomain);
        status = {'status': True, 'head': head, 'logs': self.logs}
        json.dump(status, open('logs/%s/%s_log.json' % (subdomain, job_id), 'w'))

        # Tell the main site we're done
        self.post("https://appcloudy.com/deploy_finished/%s_%s/" % (subdomain, job_id), {'head': head})


if __name__ == '__main__':
    folder = sys.argv[1]
    job_id = sys.argv[2]

    c = Compiler('apps/%s' % folder, folder, job_id)

