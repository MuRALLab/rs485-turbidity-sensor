#!/usr/bin/env bash

# net-provision.sh
# Provisions network for field deployment: Static LAN + WiFi with Cloud-Init override.

set -e

# 1. Disable Cloud-Init Network Overrides
echo "[INFO] Disabling Cloud-Init network configuration..."
echo "network: {config: disabled}" | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg

# 2. Update the Netplan Configuration
echo "[INFO] Overwriting /etc/netplan/50-cloud-init.yaml..."
sudo tee /etc/netplan/50-cloud-init.yaml > /dev/null <<EOF
network:
    version: 2
    renderer: networkd
    ethernets:
        eth0:
            dhcp4: no
            addresses:
                - 192.168.1.50/24
            optional: true
    wifis:
        wlan0:
            dhcp4: true
            optional: true
            access-points:
                Guest:
                    password: "<password>"
EOF

# 3. Apply the Configuration
echo "[INFO] Applying network settings..."
sudo netplan apply

echo "[SUCCESS] Configuration applied."
echo "[REMINDER] Ensure your PC Ethernet is set to 192.168.1.51 (Subnet: 255.255.255.0)."