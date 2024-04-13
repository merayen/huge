# Huge
Version control and off-site replication tool dealing with big files. Inspired by git.

Uses SSH or local storage, but S3 support and other plain storages are planned.
Native git integration planned.

## Example
```
$ huge init
$ touch big_file.dat
$ huge add big_file.dat
$ huge status
Staged for commit:
  A big_file.dat

Not staged for commit:
  A .hugeignore
$ huge commit -m "My first commit"
$ huge log
d52549163e397e7014cbc69d8897a67b 2024-04-13 15:35 100%/100% My first commit
$ huge send login@server:path/my_project
$ huge log
d52549163e397e7014cbc69d8897a67b 2024-04-13 15:35 100%/100% My first commit
$ huge push
$ huge log
d52549163e397e7014cbc69d8897a67b 2024-04-13 15:35 100%/200% My first commit
$ huge drop
$ huge log
d52549163e397e7014cbc69d8897a67b 2024-04-13 15:35 0%/100% My first commit
```
