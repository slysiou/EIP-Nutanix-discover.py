
import urllib3
import requests
import hashlib
import json
from base64 import b64encode
import configparser
import time
from datetime import datetime, timedelta
import os

start_time = datetime.now()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

output = []
config = configparser.ConfigParser()
config.read('config.ini')
request_url = config['nutanix']['url']
username = config['nutanix']['user']
password = config['nutanix']['password']

encoded_credentials = b64encode(bytes(f'{username}:{password}',
encoding='ascii')).decode('ascii')
auth_header = f'Basic {encoded_credentials}'
payload = '{ "length": 2000 }'
headers = {
    'Accept': 'application/json', 
    'Content-Type': 'application/json',
    'Authorization': f'{auth_header}', 
    'cache-control': 'no-cache'}

# Worker
ts = int(time.time())
worker = { 
    'type': 'worker',
    'ts': f"{ts}",
    'uuid': config['eip']['uuid']
    }
output.append(worker)

# Folders
response = requests.request('post', request_url + '/clusters/list', data=payload, headers=headers,
verify=False)
if response.status_code == 200:
    entities = response.json()['entities']
    for ent in entities:
        if ent["spec"]['name'] != 'Unnamed':
            folder = { 'type':  'folder', 'status': 'ok'}
            folder['id'] = ent["metadata"]['uuid'] 
            folder['name'] = ent["spec"]['name']
            output.append(folder)
            # print(json.dumps(ent['status'], indent=1))
else:
    print("Error: can't find folders")
    exit()
# Network
response = requests.request('post', request_url + '/subnets/list', data=payload, headers=headers,
verify=False)
if response.status_code == 200:
    entities = response.json()['entities']
    for ent in entities:
        network = { 'type':  'network', 'status': 'ok'}
        network['folder_id'] = ent['status']["cluster_reference"]['uuid'] 
        network['id'] = ent["metadata"]['uuid'] 
        network['name'] = ent["spec"]['name']
        output.append(network)
        # print(json.dumps(ent['status'], indent=1))
else:
    print("Error: can't find Network")
    exit()

# Instances
response = requests.request('post', request_url + '/vms/list', data=payload, headers=headers,
verify=False)
if response.status_code == 200:
    entities = response.json()['entities']
    for ent in entities:
        vm = { 'type':  'instance'}
        vm['folder_id'] = ent['status']["cluster_reference"]['uuid'] 
        vm['id'] = ent['metadata']['uuid']
        vm['name'] = ent['status']['name']
        vm['status'] = ent['status']["resources"]['power_state']
        vm['cpu'] = ent['status']["resources"]['num_sockets']
        vm['ram'] = ent['status']["resources"]['memory_size_mib']
        if ent['metadata'].get('project_reference') is not None:
            vm['parameters']= { 'project_reference': ent['metadata']['project_reference']['name']}
        output.append(vm)

        # ip linknetworkinstance
        for nic in ent['status']["resources"]['nic_list']:
            # linknetworkinstance
            lni = { 'type': 'linknetworkinstance'}
            lni['network_id'] = nic['subnet_reference']['uuid']
            lni['instance_id'] = nic['uuid']
            output.append(lni)
            # ip
            ip = { 'type': 'ip'}
            ip['folder_id'] = vm['folder_id']
            ip['mac'] = nic['mac_address']
            ip['status'] = 'ok' if nic['is_connected'] else 'nok'


            for ipv4 in nic['ip_endpoint_list']:
                ip['addr4'] = ipv4['ip']
                # ip['addr6'] =
                hash = hashlib.md5(ip['addr4'].encode()).hexdigest()[0:9]
                ip['id'] = f"{nic['uuid']}-{hash}"
                output.append(ip)

                # linkipinstance
                lii = { 'type': 'linkipinstance'}
                lii['ip_id'] = ip['id']
                lii['instance_id'] = vm['id']
                output.append(lii)

                # linkipnetwork
                lin = { 'type': 'linkipnetwork'}
                lin['ip_id'] = ip['id']
                lin['network_id'] = lni['network_id']
                output.append(lin)

else:
    print("Error: can't find VMs")
    exit()

# Write file
output.append(
    {"type": "result", "errcode": "1", "message": "OK"})
output.append(
    {"type": "worker", "duration": "1"}
)

file = open(
    f"{config['eip']['uuid']}.{ts}", "w")
for l in output:
    file.write(json.dumps(l))
    file.write("\n")
file.close()

# End
end_time = datetime.now()
print(f'Generation completed, total runtime {end_time - start_time}')

# Send file
print("Start sending...")
print('scp %s.%s %s@%s:%s' % 
                 (config['eip']['uuid'],ts, config['eip']['user'], config['eip']['ip'], config['eip']['path']) )
exec = os.system('scp %s.%s %s@%s:%s' % 
                 (config['eip']['uuid'],ts, config['eip']['user'], config['eip']['ip'], config['eip']['path']) )

if (exec == 0):
    print(f'File sent!')
else:
    print("Error sending file")

os.unlink('%s.%s' % ((config['eip']['uuid'],ts)))