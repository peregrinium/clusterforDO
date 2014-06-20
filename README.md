Creating a cluster on Digital Ocean - CoreOS style
=========

Digital Ocean is a cool cloud provider that sells ridiculously cheap SSD cloud servers. However they do not support custom images or the awesome CoreOS. Lets build a cluster of cloud servers with the CoreOS tools.

The Components
---------
  - Etcd: A distributed key/value store, accessible over HTTP. Used to communicate within the cluster.
  - Fleet: A distributed init system, based on systemd. Used to manage jobs within the cluster.
  - Docker: A linux container system, used to isolate services without the VM overhead.

Requirements
---------
  - Debian 7 x64 droplet(s) with:
     - The same availablity zone
     - Private networking enabled
     - Any size
  - A local machine with:
     - Python 2.7
     - Pip

Usage
---------
Install fabric
```
pip install fabric
```
Clone the repo
```
git clone https://github.com/peregrinium/clusterforDO.git clusterfordo
cd clusterfordo
```
Provision the server (you can get a discovery url from https://discovery.etcd.io/new)
```
fab provision:host=[ip],discovery_url=[https://discovery.etcd.io/TOKEN]
```
You can also supply metadata for this node (for example a usage type). Make sure you escape the "=" and ",".
```
fab provision:host=[ip],discovery_url=[https://discovery.etcd.io/TOKEN],metadata="type\=app"
```
If your output ends with:
```
[x.x.x.x] run: systemctl start fleet.service

Done.
Disconnecting from x.x.x.x... done.
```
SSH into your server and execute the the following command:
```
root@hostname:# fleetctl list-machines
```
You should see this:
```
MACHINES            IP          METADATA
xxxxxxx....         x.x.x.x     [your metadata]
```
Repeat this for every server you want to add to the cluster (with the same discovery_url, or else you are creating different clusters). You should see more lines when you list the machines after adding more nodes to the cluster.

**_If you have configured the entire cluster, encrypt or remove `ssh/rsa_id`._**

What does the script do?
----
The script is based on fabric, which basically makes ssh connections to a machine and executes defined commands. The script does the following.

  - Update the system
  - Switch debian from sysv to systemd (and reboot)
  - Regenerate the machine-id (Digital Ocean always uses the same id)
  - Create the `core` user (with `sudo` permissions) and generate ssh keys for that user
  - Create the `docker` group and add the `core` user to it
  - Install and configure ufw (firewall) so that:
     - The internal interface can access etcd
     - The docker bridge can access etcd
     - Only SSH is allowed from the public interface
  - Install and configure etcd
  - Install and configure docker
  - Install and configure fleet

How can I change configuration?
----
Changing the configuration is at your own risk (actually, so is using this script). The `configs` folder contains templates that the script uses. You can change these at your own volition, however there are reserverd keywords that you can either use or should avoid when adding your own parameters. The `ssh` folder contains a script to generate keys for the `core` user.

#### etcd.conf
Parameters:
  - `INT_IP`: This is replaced with the interal ip of your server (`eth1`)
  - `DISCOVERY_ETCD`: This is replaced with your discovery url
  - `NAME_ETCD`: This is replaced with your FQDN hostname (`hostname -f`)

#### fleet.conf
Parameters:
  - `INT_IP`: This is replaced with the interal ip of your server (`eth1`)
  - `METADATA_FLEET`: This is replaced with the unescaped metadata variable

#### ssh keys
ssh keys are generated at your computer the first time you run this script. The script checks if `rsa_id` and `rsa_id.pub` contain `"UNGENERATED"`, if so it generates new keys. You can use keys you have generated yourself by just entering them into the file. The script will never touch actual keys.

**_If you have configured the entire cluster, encrypt or remove `ssh/rsa_id`._**

#### services
The `services` folder contains service files for systemd, these are copied directly and not parsed. If you need to edit these, and you probably dont, go ahead. 


How do I use my new fancy pants cluster?
----
I kindly refer you to the internet: https://coreos.com/docs/launching-containers/launching/fleet-using-the-client/

License
----
MIT
