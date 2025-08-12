#!/bin/bash
set -e

echo "Generating ru_RU.UTF-8 locale..."
sed -i '/ru_RU.UTF-8/s/^#//' /etc/locale.gen
locale-gen
localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8
echo "Locale ru_RU.UTF-8 generated successfully"
