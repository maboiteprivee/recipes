from cuisine import package_ensure, mode_sudo, package_update, file_exists
from fabric.api import env, local
from fabric.contrib.files import upload_template
from fabric.operations import get, run, cd, sudo
from fabric.utils import puts
from fabric.colors import red, green

ROUNDCUBE_URL = 'http://downloads.sourceforge.net/project/roundcubemail/roundcubemail/0.9.2/roundcubemail-0.9.2.tar.gz'

def vagrant():
  "Use Vagrant for testing"
  env.user = 'vagrant'
  env.hosts = ['127.0.0.1:2222']  
  # retrieve the IdentityFile:
  result = local('vagrant ssh-config | grep IdentityFile', capture=True)
  env.key_filename = result.lstrip('IdentityFiles').strip() # parse IdentityFile
 
def setup():
    base_tools = ['vim', 'git-core', 'build-essential']
    web = ['nginx', 'php5-fpm', 'sqlite3', 'php5-sqlite', 'php5-apc']
    mail = ['dovecot-imapd', 'postfix']

    puts(green("Installing base packages..."))
    package_update()
    for p in base_tools+web+mail :
        package_ensure(p)
 
    puts(green("Installing Roundcube..."))
    rc_filename = ROUNDCUBE_URL.split('/'[-1])
    with mode_sudo():
        run("mkdir /var/www")
        cd("/var/www")
        run("wget %s" % ROUNDCUBE_URL)
        run("tar xfz %s" % rc_filename)
        run("rm %s" % rc_filename)
        run("mv %s roundcube" % rc_filename)
        run("chown -R www-data:www-data")
        #TODO roundcube config files (template)
    
    puts(green("Configuring Nginx..."))
    with mode_sudo():
        if file_exists('/etc/nginx/sites-enabled/default'):
            run('rm /etc/nginx/sites-enabled/default')
        # TODO virtual host (template)
    
    #upload_template()