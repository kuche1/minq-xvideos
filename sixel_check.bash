#!/usr/bin/env bash

# shamelessly stolen from
# https://github.com/hackerb9/lsix/blob/master/lsix

# IS TERMINAL SIXEL CAPABLE?		# Send Device Attributes
IFS=";" read -a REPLY -s -t 1 -d "c" -p $'\e[c' >&2

for code in "${REPLY[@]}"; do
	if [[ $code == "4" ]]; then
	    hassixel=yes
	    break
	fi
done

if [ "$hassixel" == "yes" ]; then
	exit 0
else
	exit 1
fi
