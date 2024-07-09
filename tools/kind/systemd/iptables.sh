#!/usr/bin/env bash

set -e

# Wait for kindnetd to create its rule
RETRIES=10
while ! iptables -t nat -L KIND-MASQ-AGENT 2>/dev/null; do
    echo "waiting for KIND-MASQ-AGENT chain"
    sleep 5
    [[ $((RETRIES--)) -eq 0 ]] && { echo "stopped waiting for creation of KIND-MASQ-AGENT iptables chain"; exit 1; }
done

for prefix in 192.168.10.0/24 192.168.100.0/24; do
    if ! iptables -t nat -L KIND-MASQ-AGENT | grep -q ${prefix}; then
        iptables -t nat -I KIND-MASQ-AGENT 1 -s ${prefix} -d ${prefix} -m comment --comment "Avoid masquerading inside libvirt-metal networks" -j RETURN
    fi
done

echo "libvirt-metal networks rules successfully added to KIND-MASQ-AGENT chain"
