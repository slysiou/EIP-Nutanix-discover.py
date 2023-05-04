# EfficientIP Cloud Observer external plugin for Nutanix

Get information from Prism Element or Prism Central and generate data file for EfficientIP Cloud Observer.

The generated file must be pushed to the /data1/tmp/cloud_observer/ of the EfficientIP SOLIDserver to be integrated through the normal croned job (every minute).

## Documentation

Nutanix API v3 is available on [Nutanix developper website](https://www.nutanix.dev/api_references/prism-central-v3/)

Swagger in also available on Prism UI. By default v2 is presented. Change URL to v3 to see it.

## config.ini

Use the sample file to create a `config.ini`.

like:
```ini
[nutanix]
user=admin
password=pass
url=https://prism.local:9440/api/nutanix/v3

[eip]
uuid=DBCDFED3-994D-4F51-9605-C5799DD5B929
```

## Objects imported

### Folder

Folder name is based on cluster name.

### Instance

Instance name is based on VM name (excluding Nutanix CVM).

### Network

Network name is based on Nutanix Subnet defined on the cluster.

### IPs

Each VM Network interface has 1 Mac address, multiple IP addresses connected to 1 Network.

## Installation

- Install python3
- Create an environment and activate it ([venv documentation](https://docs.python.org/fr/3/library/venv.html))
- Install required packages with:
```sh
pip install -r requirements.txt
````

## Run the script

```sh
python main.py
```