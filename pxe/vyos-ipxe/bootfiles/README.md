# VyOS bootfiles for PXE

Normally, this folder should contain three files, required for booting via PXE:

- `filesystem.squashfs` - root filesystem
- `initrd.img` - initramfs
- `vmlinuz` - Linux kernel

## Getting files

- If you only need to install VyOS via PXE, you may get these files from an ISO image.
- If you want to load VyOS with a configuration via PXE (for example, to use without installation), you may get all three files, using [Ansible playbook](https://github.com/zdc/vyos-vm-images/tree/fix-qemu-01) with the next settings:
  ```
  ansible-playbook qemu.yml -e iso_local=/tmp/vyos/custom_image.iso -e cloud_init=true -e cloud_init_ds=NoCloud,None -e pxe=true
  ```
  Then, an archive with files will be located in the /tmp/ directory.
  Optionally, you may add the `-e keep_user=true` option to keep the `vyos` user for debugging purposes.
