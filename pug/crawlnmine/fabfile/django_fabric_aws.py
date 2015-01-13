''' 
--------------------------------------------------------------------------------------
django_fabric_aws.py
--------------------------------------------------------------------------------------
A set of fabric commands to manage a Django deployment on AWS

author : Ashok Fernandez (github.com/ashokfernandez/)
credit : Derived from files in https://github.com/gcollazo/Fabulous
date   : 11 / 3 / 2014

Commands include:
    - fab spawn instance  
        - Spawns a new EC2 instance (as definied in project_conf.py) and return's it's public dns
          This takes around 8 minutes to complete.
 
    - fab update_packages
        - Updates the python packages on the server to match those found in requirements/common.txt and 
          requirements/prod.txt
 
    - fab deploy
        - Pulls the latest commit from the master branch on the server, collects the static files, syncs the db and                   
          restarts the server
 
    - fab reload_gunicorn
        - Pushes the gunicorn startup script to the servers and restarts the gunicorn process, use this if you 
          have made changes to templates/start_gunicorn.bash
 
    - fab reload_nginx
        - Pushes the nginx config files to the servers and restarts the nginx, use this if you 
          have made changes to templates/nginx-app-proxy or templates/nginx.conf

    - fab reload_supervisor
        - Pushes the supervisor config files to the servers and restarts the supervisor, use this if you 
          have made changes to templates/supervisord-init or templates/supervisord.conf
    
    - fab manage:command="management command"
        - Runs a python manage.py command on the server. To run this command we need to specify an argument, eg for syncdb
          type the command -> fab manage:command="syncdb --no-input"

'''

from fabric.api import *
from fabric.colors import green as _green, yellow as _yellow
from project_conf import *
import tasks
import boto
import boto.ec2
import time

# AWS user credentials
env.user = fabconf['SERVER_USERNAME']
env.key_filename = fabconf['SSH_PRIVATE_KEY_PATH']

# List of EC2 instances to work on
env.hosts = fabconf['EC2_INSTANCES']
         
# ------------------------------------------------------------------------------------------------------------------
# MAIN FABRIC TASKS - Type fab <function_name> in the command line to execute any one of these
# ------------------------------------------------------------------------------------------------------------------

def spawn():
    env.hosts = []

def instance():
    """
    Creates an EC2 instance from an Ubuntu AMI and configures it as a Django server
    with nginx + gunicorn
    """
    # Record the starting time and print a starting message
    start_time = time.time()
    print(_green("Started..."))

    # Use boto to create an EC2 instance
    env.host_string = _create_ec2_instance()
    print(_green("Waiting 30 seconds for server to boot..."))
    time.sleep(30)
    
    # Configure the instance that was just created
    for item in tasks.configure_instance:
        try:
            print(_yellow(item['message']))
        except KeyError:
            pass
        globals()["_" + item['action']](item['params'])
    
    # Print out the final runtime and the public dns of the new instance
    end_time = time.time()
    print(_green("Runtime: %f minutes" % ((end_time - start_time) / 60)))
    print(_green("\nPLEASE ADD ADDRESS THIS TO YOUR ")),
    print(_yellow("project_conf.py")),
    print(_green(" FILE UNDER ")),
    print(_yellow("fabconf['EC2_INSTANCES'] : ")),
    print(_green(env.host_string))

def deploy():
    """
    Pulls the latest commit from bitbucket, resyncs the database, collects the static files and restarts the
    server.
    """
    _run_task(tasks.deploy, "Updating server to latest commit in the bitbucket repo...", "Finished updating the server")

def update_packages():
    """
    Updates the python packages on the server as defined in requirements/common.txt and 
    requirements/prod.txt
    """
    _run_task(tasks.update_packages, "Updating server packages with pip...", "Finished updating python packages")

def reload_nginx():
    """
    Reloads the nginx config files and restarts nginx
    """
    _run_task(tasks.reload_nginx, "Reloading the nginx config files...", "Finished reloading nginx")

def reload_supervisor():
    """
    Reloads the supervisor config files and restarts supervisord
    """
    _run_task(tasks.reload_supervisor, "Reloading the supervisor config files...", "Finished reloading supervisor")

def reload_gunicorn():
    """
    Reloads the Gunicorn startup script and restarts gunicorn
    """
    _run_task(tasks.reload_gunicorn, "Reloading the gunicorn startup script...", "Finished reloading the gunicorn startup script")

def manage(command):
    """
    Runs a python manage.py command on the server
    """
    
    # Get the instances to run commands on
    env.hosts = fabconf['EC2_INSTANCES']

    # Run the management command insite the virtualenv
    _virtualenv("python %(PROJECT_PATH)s/manage.py " + command)


# ------------------------------------------------------------------------------------------------------------------
# SUPPORT FUNCTIONS
# ------------------------------------------------------------------------------------------------------------------

def _run_task(task, start_message, finished_message):
    """
    Tasks a task from tasks.py and runs through the commands on the server
    """

    # Get the hosts and record the start time
    env.hosts = fabconf['EC2_INSTANCES']
    start = time.time()

    # Check if any hosts exist
    if env.hosts == []:
        print("There are EC2 instances defined in project_conf.py, please add some instances and try again")
        print("or run 'fab spawn_instance' to create an instance")
        return

    # Print the starting message
    print(_yellow(start_message))

    # Run the task items
    for item in task:
        try:
            print(_yellow(item['message']))
        except KeyError:
            pass
        globals()["_" + item['action']](item['params'])

    # Print the final message and the elapsed time
    print(_yellow("%s in %.2fs" % (finished_message, time.time() - start)))

def _create_ec2_instance():
    """
    Creates EC2 Instance
    """
    print(_yellow("Creating instance"))
    conn = boto.ec2.connect_to_region(ec2_region, aws_access_key_id=fabconf['AWS_ACCESS_KEY'], aws_secret_access_key=fabconf['AWS_SECRET_KEY'])

    image = conn.get_all_images(ec2_amis)

    reservation = image[0].run(1, 1, ec2_keypair, ec2_secgroups,
        instance_type=ec2_instancetype)

    instance = reservation.instances[0]
    conn.create_tags([instance.id], {"Name":fabconf['INSTANCE_NAME_TAG']})
    
    while instance.state == u'pending':
        print(_yellow("Instance state: %s" % instance.state))
        time.sleep(10)
        instance.update()

    print(_green("Instance state: %s" % instance.state))
    print(_green("Public dns: %s" % instance.public_dns_name))
    
    return instance.public_dns_name

def _virtualenv(params):
    """
    Allows running commands on the server
    with an active virtualenv
    """
    with cd(fabconf['APPS_DIR']):
        _virtualenv_command(_render(params))

def _apt(params):
    """
    Runs apt-get install commands
    """
    for pkg in params:
        _sudo("apt-get install -qq %s" % pkg)

def _pip(params):
    """
    Runs pip install commands
    """
    for pkg in params:
        _sudo("pip install %s" % pkg)

def _run(params):
    """
    Runs command with active user
    """
    command = _render(params)
    run(command)

def _sudo(params):
    """
    Run command as root
    """
    command = _render(params)
    sudo(command)

def _put(params):
    """
    Moves a file from local computer to server
    """
    put(_render(params['file']), _render(params['destination']))

def _put_template(params):
    """
    Same as _put() but it loads a file and does variable replacement
    """
    f = open(_render(params['template']), 'r')
    template = f.read()

    run(_write_to(_render(template), _render(params['destination'])))

def _render(template, context=fabconf):
    """
    Does variable replacement
    """
    return template % context

def _write_to(string, path):
    """
    Writes a string to a file on the server
    """
    return "echo '" + string + "' > " + path

def _append_to(string, path):
    """
    Appends to a file on the server
    """
    return "echo '" + string + "' >> " + path

def _virtualenv_command(command):
    """
    Activates virtualenv and runs command
    """
    with cd(fabconf['APPS_DIR']):
        sudo(fabconf['ACTIVATE'] + ' && ' + command, user=fabconf['SERVER_USERNAME'])
