# Cloud-init User-Data

You may use Cloud-init User-Data to provide any custom configuration to a VyOS instance during deployment.

## Preparation

You need to have Python3 and write-mime-multipart script installed. If you do not have installed Cloud-init, you may fetch write-mime-multipart from the cloud-utils repository:
```
wget https://git.launchpad.net/cloud-utils/plain/bin/write-mime-multipart
```

### Configuration syntax

All configuration commands MUST be entered according to the next rules:

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

### Commands list
If you need to configure not very many options, you may enter commands directly to the `vyos-config.txt` file.

### URL
You may place a text file with commands to an HTTP server, available to a deployed instance during startup. In this case, inside the `vyos-config.txt` file you need to enter only the direct URL of this file. We strongly recommend using unencrypted HTTP and IP address as a target URL to avoid problems with DNS and certificates.

## Creating User-Data

When your commands list will be prepared, you need to convert it to the User-Data format. Use the next command for this:

```
python3 write-mime-multipart vyos-handler.py vyos-config.txt
```
All the output is your User-Data, which should be used during startup.

## Troubleshooting

- User-Data maximum size is ~16384 bytes. You need to be sure that your User-Data is inside this limit. We recommend you to switch to the HTTP URL in case if your User-Data is 15000 bytes or more, to avoid any problems. To get the size of User-Data you may use the next command:
  ```
  python3 write-mime-multipart vyos-handler.py vyos-config.txt | wc -c
  ```
  The output will be the size.
  Some deployments cannot use HTTP sources, but able to fetch User-Data from a local file. You may try to compress it to gzip archive:
  ```
  python3 write-mime-multipart vyos-handler.py vyos-config.txt -z > user-data.gz
  ```
- Some of the clouds (for example AWS) and hypervisors can use gzipped User-Data, encoded with base64. You may get it with:
  ```
  python3 write-mime-multipart vyos-handler.py vyos-config.txt -z | base64
  ```
- If something does not work as expected, you may catch logs from the instance after deployment with:
  ```
  sudo journalctl | grep -E 'part-handler-000|cloud-init'
  ```

## Usage

### Google Cloud Engine

Add to the instance Metadata key "user-data" with generated User-Data as value.

### Amazon Web Services

Add to the instance User data your generated User-Data as text.

### Exoscale

Add to the instance User Data your generated User-Data.