#!/bin/bash

image=${1}
uuid=${2}
from=${3}
to=${4}

i=0

tmp_dir=$(mktemp -d)

while 1; do
    if [ ! -f "/dev/nbd${i}"]; then
        break
    fi
    i=((i + 1))
done

qemu-nbd --connect="/dev/nbd${i}" "${image}"

mount UUID="${uuid}" "${tmp_dir}"

cp -R -v "${from}" "${tmp_dir}${to}"

if umount "${tmp_dir}"; then
    rm -f -d "${tmp_dir}"
fi


