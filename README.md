# Cloud-init User-Data

You may use Cloud-init User-Data to provide any custom configuration to a VyOS instance during deployment.

## Quick and easy way

If an instance has access to the Internet during deployment, you may fill User-Data field with:
```
#include-once
https://raw.githubusercontent.com/zdc/vyos-cloud-init-userdata/master/vyos_handler.py
http://192.0.2.1/vyos-config.txt
```
where `http://192.0.2.1/vyos-config.txt` is URL to the file with content, supported by part-handler (see details below).

Also, you may serve the `vyos_handler.py` at your own HTTP server in the same way, if the Internet is not available or DNS does not work at the deployment stage.

If your instance cannot use the HTTP server as a configuration source, or you want to provide the whole configuration directly inside the User-Data, you need to prepare it according to the information provided below.

## Preparation

You need to have Python3 and write-mime-multipart script installed. If you do not have installed Cloud-init, you may fetch write-mime-multipart from the cloud-utils repository:
```
wget https://git.launchpad.net/cloud-utils/plain/bin/write-mime-multipart
```

## User-Data configuration syntax

The part-handler support three types of User-Data:

 - URL
 - complete VyOS configuration
 - list of configuration commands

### URL
You may place a text file with configuration file or commands list to an HTTP server, available to a deployed instance during startup. In this case, inside the `vyos-config.txt` file you need to enter only the direct URL of this file. We strongly recommend using unencrypted HTTP and IP address as a target URL to avoid problems with DNS and certificates.

### Complete configuration

You may provide a complete configuration file inside User-Data. The file MUST be exactly in the same format, as VyOS save. You may simply copy the `/config/config.boot` file content of preconfigured VyOS to be sure. We do not recommend using MAC addresses to interface name binding inside the config (the `hw-id` option) if you are not pretty sure that you need this.

If the complete configuration file will be provided, the VyOS startup configuration will be fully replaced by them.

### Commands list

If you need to configure not very many options, you may enter commands directly to the `vyos-config.txt` file. All configuration commands MUST be entered according to the next rules:

 - one command per line
 - no empty lines allowed
 - if command ending by value, it must be inside **single** quotes: `'example_value'`
 - a single-quote symbol is not allowed inside command or value

The best way how to get proper formatting is to configure all the commands on a test router, then run on it:
```
show configuration commands
```
And copy wanted commands from the output.

You have two options on how to provide configuration commands:

## Creating User-Data

When your commands list will be prepared, you need to convert it to the User-Data format. Use the next command for this:

```
python3 write-mime-multipart vyos_handler.py vyos-config.txt
```
All the output is your User-Data, which should be used during startup.

## Multiple tasks

You may apply multiple tasks via User-Data. For example, can be created three files:

`vyos-config1.txt` - with URL to the file with the complete configuration

`vyos-config2.txt` - with URL to the file with a commands list

`vyos-config3.txt` - with a commands list

And they all can be combined with:
```
python3 write-mime-multipart vyos_handler.py vyos-config1.txt vyos-config2.txt vyos-config3.txt
```
During the boot, VyOS will apply all of them in sequence.

## Troubleshooting

- User-Data maximum size is ~16384 bytes. You need to be sure that your User-Data is inside this limit. We recommend you to switch to the HTTP URL in case if your User-Data is 15000 bytes or more, to avoid any problems. To get the size of User-Data you may use the next command:
  ```
  python3 write-mime-multipart vyos_handler.py vyos-config.txt | wc -c
  ```
  The output will be the size.
  Some deployments cannot use HTTP sources, but able to fetch User-Data from a local file. You may try to compress it to gzip archive:
  ```
  python3 write-mime-multipart vyos_handler.py vyos-config.txt -z > user-data.gz
  ```
- Some of the clouds (for example AWS) and hypervisors can use gzipped User-Data, encoded with base64. You may get it with:
  ```
  python3 write-mime-multipart vyos_handler.py vyos-config.txt -z | base64
  ```
- If something does not work as expected, you may catch logs from the instance after deployment with:
  ```
  cat /var/log/cloud-init.log | tee
  ```

## Usage

### VMware ESXi

Generate a User-Data with:
```
python3 write-mime-multipart vyos_handler.py vyos-config.txt -z | base64 -w 0
```
And paste it to the User-Data field during OVA template deployment. Do not forget about a size limit - it is better to check a User-Data size with `| wc -c` before adding it to the instance.

### Google Cloud Engine

Add to the instance Metadata key "user-data" with generated User-Data as value.

### Amazon Web Services

Add to the instance User data your generated User-Data as text.

### Exoscale

Add to the instance User Data your generated User-Data.

### With PXE boot

See the instruction in the [pxe folder](pxe/README.md).


## Integration into Cloud-init package

Instruction can be found [here](cloud-init/README.md).