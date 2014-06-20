#!/usr/bin/python

from fabric.api import *
from fabric.contrib.files import sed

env.user="root"

def provision(discovery_url=None,metadata=None):
    if discovery_url is None:
        abort("A discovery url is required for cluster joining," \
              "if this is the first machine, create one at https://discovery.etcd.io/new")
    update_and_upgrade()
    switch_to_systemd()
    regenerate_machine_id()
    create_users()
    install_and_configure_firewall()
    install_etcd(discovery_url)
    install_docker()
    install_fleet(metadata)
    cleanup()

def update_and_upgrade():
    run("DEBIAN_FRONTEND=noninteractive")
    with hide('stdout', 'stderr'):
        run("apt-get update && apt-get upgrade -y")

def switch_to_systemd():
    with hide('stdout', 'stderr'):
        run("echo \"Yes, do as I say!\" | apt-get install -y -q --force-yes systemd-sysv systemd")
    reboot(wait=30)

def regenerate_machine_id():
    run("chmod o+w /etc/machine-id")
    run("< /dev/urandom tr -dc a-f0-9 | head -c32 > /etc/machine-id")
    run("chmod o-w /etc/machine-id")

def install_and_configure_firewall():
    run("apt-get install ufw")
    run("yes | echo ufw enable")
    run("ufw default deny")
    run("ufw allow 22")
    run("ufw allow in on eth1 to any port 4001")
    run("ufw allow in on eth1 to any port 7001")
    run("ufw allow in on docker0 to any port 4001")
    run("ufw allow in on docker0 to any port 7001")
    
def create_users():
    run("groupadd docker")
    run("useradd -U -m core -G sudo,docker")
    with lcd("ssh"):
        local("python keygen.py")
        run("mkdir /home/core/.ssh")
        put("id_rsa","/home/core/.ssh/id_rsa")
        put("id_rsa.pub","/home/core/.ssh/id_rsa.pub")
        run("touch /home/core/.ssh/authorized_keys")
        run("cat /home/core/.ssh/id_rsa.pub >> /home/core/.ssh/authorized_keys")
        run("chown -R core:core /home/core/.ssh")
        run("chmod 700 /home/core/.ssh")
        run("chmod 600 /home/core/.ssh/id_rsa")
        run("chmod 600 /home/core/.ssh/authorized_keys")
        run("chmod 644 /home/core/.ssh/id_rsa.pub")
    
def install_etcd(discovery_url):
    run("mkdir -p /var/configuration/temp")
    with cd("/var/configuration/temp"):
        run("wget https://github.com/coreos/etcd/releases/download/v0.4.1/etcd-v0.4.1-linux-amd64.tar.gz")
        run("tar -xvzf etcd-v0.4.1-linux-amd64.tar.gz")
        with cd("/var/configuration/temp/etcd-v0.4.1-linux-amd64"):
            run("cp etcd /usr/bin/etcd")
            run("cp etcdctl /usr/bin/etcdctl")
    run("chmod og+x /usr/bin/etcd")
    run("chmod og+x /usr/bin/etcdctl")
    run("rm -rf /var/configuration/temp/etcd-v0.4.1-linux-amd64")
    run("mkdir /etc/etcd")
    with cd("/etc/etcd"):
        with lcd("configs"):
            put("etcd.conf","etcd.conf")
        int_ip = run("echo $(/sbin/ifconfig |grep -B1 'inet addr' |awk '{ if ( $1 == \"inet\" ) { print $2 } else if ( $2 == \"Link\" ) { printf \"%s:\" ,$1 } }' |awk -F: '{ print $3 }' | grep -E '(192\.168|10\.)')")
        hostname = run("echo $(hostname -f)")
        sed("etcd.conf", "INT_IP", int_ip)
        sed("etcd.conf", "NAME_ETCD", hostname)
        sed("etcd.conf", "DISCOVERY_ETCD", discovery_url)
    create_service("etcd")

def install_docker():
    run("echo deb http://get.docker.io/ubuntu docker main | tee /etc/apt/sources.list.d/docker.list")
    run("apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9")
    with hide('stdout', 'stderr'):
        run("apt-get update")
        run("apt-get install -y lxc-docker")
    create_service("docker")
    
def install_fleet(metadata):
    with cd("/var/configuration/temp"):
        run("wget https://github.com/coreos/fleet/releases/download/v0.3.3/fleet-v0.3.3-linux-amd64.tar.gz")
        run("tar -xvzf fleet-v0.3.3-linux-amd64.tar.gz")
        with cd("/var/configuration/temp/fleet-v0.3.3-linux-amd64"):
            run("cp fleet /usr/bin/fleet")
            run("cp fleetctl /usr/bin/fleetctl")
    run("chmod og+x /usr/bin/fleet")
    run("chmod og+x /usr/bin/fleetctl")
    run("rm -rf /var/configuration/temp/fleet-v0.3.3-linux-amd64")
    run("mkdir /etc/fleet")
    with cd("/etc/fleet"):
        with lcd("configs"):
            put("fleet.conf","fleet.conf")
        int_ip = run("echo $(/sbin/ifconfig |grep -B1 'inet addr' |awk '{ if ( $1 == \"inet\" ) { print $2 } else if ( $2 == \"Link\" ) { printf \"%s:\" ,$1 } }' |awk -F: '{ print $3 }' | grep -E '(192\.168|10\.)')")
        sed("fleet.conf","INT_IP",int_ip)
           
        if metadata is not None:
            sed("fleet.conf","METADATA_FLEET",metadata)
    create_service("fleet")
    
def create_service(name=None):
    if name is None:
        abort("Tried to create an unknown service.")
    with lcd("services"):
        put("%s.service" % name,"/etc/systemd/system/%s.service" % name)
        run("systemctl enable %s.service" % name)
        run("systemctl start %s.service" % name)
        
def cleanup():
    run("rm -rf /var/configuration")
    
