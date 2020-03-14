# Booting via PXE

You may boot into fully configured VyOS directly from PXE. This allows to install the system from network or run VyOS without installation and permanent storage (in-memory).

You will need:
- HTTP server
- TFTP server
- DHCP server
- iPXE loader

## Configuring

> **WARNING**
> Do not use DNS domain names in URLs inside configuration, as this is not supported by iPXE. All files must be accessible via URLs with an IP addresses.

 1. Install an HTTP server, which will be available to a VyOS instance during booting.
 2. Copy the content of `vyos-ipxe` folder to the HTTP server directory.
 3. Change IP addresses inside configuration files to proper ones and configure Cloud-init options:
     - `vyos-ipxe/vyos-ipxe.txt` - set URL to the `vyos-ipxe` folder and enable or disable Cloud-init;
     **Also, if Cloud-init enabled:**
     - `vyos-ipxe/cloud-init/cloud-config` - configure a datasource for Cloud-init;
     - `vyos-ipxe/cloud-init/user-data` - set URLs to `vyos_handler.py` and `vyos-config.txt` files;
     - `vyos-ipxe/cloud-init/vyos-config.txt` - add complete configuration file, commands list or URL to any of them to this file;
 4. Copy to the `vyos-ipxe/bootfiles/` folder all files, required for PXE boot ([check details here](vyos-ipxe/bootfiles/README.md)).
 5. Configure your DHCP server to provide information about boot options inside DHCP answers.
 6. Copy the `undionly.kpxe` file into the root of your TFTP server. You may get this file from the [official site](http://boot.ipxe.org/undionly.kpxe) or Debian [ipxe package](https://packages.debian.org/buster/ipxe).
> **Note**
> An example configuration for dnsmasq, which act as both DHCP and TFTP servers can be found in the `pxe/configs-example/` folder.

## Booting

Configure your bare-metal server or virtual machine to booting from a network with DHCP address to load into VyOS.

## Installing via PXE

> **WARNING**
> During installation all data on the selected disk will be deleted!

You also may install VyOS via PXE. To do this, you need additionally:
- Include `vyos-install.txt` to the `user-data`;
- Configure variables in the `vyos-install.txt`.

## Troubleshooting

If something do not work as expected, you need to check:
- DHCP server logs to be sure that an instance getting an IP address during the boot;
- TFTP server logs to check that an instance load ipxe loader;
- HTTP server logs to be sure that iPXE loader download configuration script, kernel and initramfs, also as the Linux kernel load rootfs file system later;
- VyOS logs if the configuration do not apply properly.
