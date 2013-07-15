import random
import string
from cuisine import *
from fabric.api import env, local
from fabric.contrib.files import upload_template
# from fabric.operations import run
from fabric.context_managers import cd
from fabric.utils import puts
from fabric.colors import red, green

ROUNDCUBE_URL = 'http://downloads.sourceforge.net/project/roundcubemail/roundcubemail/0.9.2/roundcubemail-0.9.2.tar.gz'

# tmp
DOMAIN = 'phramboise.fr'
NICE_NAME = 'Phramboise'
USERS = (['alexandre', 'password'])
IF_ETH = 'eth0'

def vagrant():
  "Use Vagrant for testing"
  env.user = 'vagrant'
  env.hosts = ['127.0.0.1:2222']  
  # retrieve the IdentityFile:
  result = local('vagrant ssh-config | grep IdentityFile', capture=True)
  env.key_filename = result.lstrip('IdentityFile').strip().strip('"') # parse IdentityFile
 

def _upload_templates(files, clean=True):
    for myfile in files:
        # if clean:
        #     file_unlink(myfile['filename'])
        upload_template(myfile['filename'], myfile['filename'], context=myfile.get('context', None), 
            use_jinja=True, template_dir='templates', use_sudo=True, backup=True, 
            mirror_local_mode=False, mode=myfile.get('mode', 0644))
        user = myfile.get('user', None)
        group = myfile.get('group', None)
        if user is not None or group is not None:
            file_ensure(myfile['filename'], owner=user, group=group)

def setup():
    try:
        puts(green('Installing base packages...'))
        base_packages() 
        puts(green('Configuring base system...'))
        system_config()
        puts(green('Creating users...'))
        users()
        puts(green('Installing Roundcube...'))
        roundcube()
        puts(green('Configuring Nginx...'))
        nginx()
        puts(green('Configuring Dovecot...'))
        dovecot()
        puts(green('Configuring Postfix...'))
        postfix()
    except Exception, e:
        puts(red('Something went wrong : %s' % e))

def base_packages():
    base_tools = ['vim', 'git-core', 'build-essential']
    web = ['nginx', 'php5-fpm', 'sqlite3', 'php5-sqlite', 'php-apc']
    mail = ['dovecot-imapd', 'postfix']

    package_update()
    for p in base_tools+web+mail :
        package_ensure(p)

def system_config():
    with mode_sudo():
        file_write('/etc/mailname', '%s\n' % DOMAIN)
        ip_addr = run("/sbin/ifconfig %s | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'" % IF_ETH)
        hline = '%s\t%s' % (ip_addr, DOMAIN)
        file_update('/etc/hosts', lambda x: text_ensure_line(x, hline))

def users():
    for user in USERS:
        user_ensure(user[0], passwd=user[1])

def roundcube():
    rc_filename = ROUNDCUBE_URL.split('/')[-1]
    with mode_sudo():
        dir_ensure('/var/www', owner='www-data', group='www-data', recursive=True)
        dir_remove('/var/www/roundcube')
        with cd('/var/www'):
            # download and unpack
            run('wget %s' % ROUNDCUBE_URL)
            run('tar xfz %s' % rc_filename)
            file_unlink(rc_filename)
            run('mv %s roundcube' % rc_filename.split('.tar.gz')[0])
            file_ensure('roundcubemail.sqlite', owner='www-data', group='www-data')

            # config files
            des_key = [random.choice(string.ascii_letters + string.digits) for n in xrange(24)]
            des_key = ''.join(des_key)
            context = {
                'rcmail_config_default_host': DOMAIN,
                'rcmail_config_support_url': 'mailto:postmaster@%s' % DOMAIN,
                'rcmail_config_des_key': des_key,
                'rcmail_config_product_name': NICE_NAME
            }
            conf_files = [
                {'filename': '/var/www/roundcube/config/main.inc.php', 'context': context, 'mode': 0644},
                {'filename': '/var/www/roundcube/config/db.inc.php', 'context': None, 'mode': 0644}
            ]
            _upload_templates(conf_files)

            # chown
            dir_ensure('roundcube', owner='www-data', group='www-data', recursive=True)

def nginx():
    with mode_sudo():
        file_unlink('/etc/nginx/sites-enabled/default')
        # file_unlink('/etc/nginx/sites-available/roundcube')
        context = {
            'nginx_server_name': DOMAIN,
        }
        nginx_conf = '/etc/nginx/sites-available/roundcube'
        conf_files = [
            {'filename': nginx_conf, 'context': context, 
                'user': 'root', 'group': 'root'},
        ]
        _upload_templates(conf_files)
        file_link(nginx_conf, nginx_conf.replace('sites-available', 'sites-enabled'))
        upstart_ensure('nginx')
        upstart_ensure('php5-fpm')

def dovecot():
    with mode_sudo():
        context = {}
        conf_files = [
            {'filename': '/etc/dovecot/dovecot.conf', 'context': context, 
                'user': 'root', 'group': 'root'},
            {'filename': '/etc/dovecot/conf.d/10-auth.conf', 'context': context, 
                'user': 'root', 'group': 'root'},
            {'filename': '/etc/dovecot/conf.d/10-mail.conf', 'context': context, 
                'user': 'root', 'group': 'root'},
        ]
        _upload_templates(conf_files)
        upstart_ensure('dovecot')

def postfix():
    with mode_sudo():
        context = {
            'postfix_myhostname': DOMAIN,
            'postfix_mydestination': DOMAIN
        }
        conf_files = [
            {'filename': '/etc/postfix/main.cf', 'context': context, 
                'user': 'root', 'group': 'root'},
        ]
        _upload_templates(conf_files)
        upstart_ensure('postfix')