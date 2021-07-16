# towerbox
A script that creates an inventory in [Ansible Tower](https://www.ansible.com/products/tower) from devices in [NetBox](https://netbox.readthedocs.io/en/stable/).

NetBox is not a supported inventory source within Ansible tower.
See the Red Hat article about it here: [Is Netbox a Supported Inventory Source Within Ansible Tower?](https://access.redhat.com/solutions/4264501)
But with this script it becomes possible!


### Example of device variables in Tower
```
ansible_host: 192.168.0.1
ansible_port: 22
ansible_user: root
netbox_device_role: firewall
netbox_platform: asa
netbox_status: active
netbox_tags:
  - tag1
  - tag2
  - tag3
```

Based on Rigel Di Scala's excellent [AWX Inventory Script example](https://gist.github.com/zedr/6979ab2fc49fe13e752a9896d6195c4d).
Modified by Farid Joubbi.


## Instructions
1. Copy the contents of towerbox.py as a custom script under Inventory Scripts in Ansible Tower.
2. Modify the variables `NETBOX_HOST_URL` and `NETBOX_AUTH_TOKEN`.
3. Create a new inventory that uses this new custom script.
4. Enjoy your new dynamic inventory.


This script is tested with Ansible Tower 3.7.4 and NetBox v2.11.7.
