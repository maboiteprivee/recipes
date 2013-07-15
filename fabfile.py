from cuisine import *
from fabric.api import *
from fabric.contrib.files import upload_template
 
def vagrant():
  "Use Vagrant for testing"
  env.user = 'vagrant'
  env.hosts = ['127.0.0.1:2222']
  
  # retrieve the IdentityFile:
  result = local('vagrant ssh-config | grep IdentityFile', capture=True)
  env.key_filename = result.lstrip('IdentityFiles').strip() # parse IdentityFile
 
def setup():
    base_tools = ['vim', 'git-core', 'build-essential']
    web = ['nginx', 'php5-fpm', 'sqlite3', 'php5-sqlite']
    mail = ['dovecot-imapd', 'postfix']
    
    for p in base_tools+web+mail :
        package_ensure(p)
 
    upload_template()