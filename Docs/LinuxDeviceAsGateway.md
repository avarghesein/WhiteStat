# Configuring Linux Device As the Gateway for a Private Network

Here RaspberryPi2 (192.168.1.5) will be the Linux Device, being configured as the new Default Gateway

![alt Pi](https://github.com/avarghesein/WhiteStat/blob/main/Docs/Linux%5BRaspberryPi%5D%20As%20Gateway.png)

## Update existing Router Settings.

#### Option1 (Router Provides DHCP, RaspberryPi as Default Gateway provides DNS)

By default your router will be the Default Gateway and serves DNS services. Change the configuration of your router so that, it will now point to the Linux Device,
as the Default Gateway (and optionally as DNS Server)

![alt Pi](https://github.com/avarghesein/WhiteStat/blob/main/Docs/WifiRouterConfigUpdatesForRaspberryPI.png)

#### Option2 (Router relays DHCP requests to Pi, RaspberryPi as Default Gateway provides both DNS and DHCP)

**NB: This mode also provides you Network FailOver Capability to Router (act as the secondary gateway), if Pi has not been available for some reason.This makes the Network Always Available.**

Update Router to Relay DHCP requests to Pi.

![alt Pi](https://github.com/avarghesein/WhiteStat/blob/main/Docs/DHCPRelayMode.jpg)

Setup Pi, with DNSMASQ utility and configure the same to return multiple default gateways (Primary: Pi, Secondary: Router)

Configuration Steps has been detailed [here](https://github.com/avarghesein/-NIX/blob/main/Raspberry%20Pi%20II%20(Buster)/NetworkFailoverWithMultipleGateways.md)


## Set Linux Device's Static IP Configuration/Gateway

Now update your Linux Device (Pi), IP to be a Static IP (here 192.168.1.5) and Gateway as the Original Gateway (here its the IP of the Wifi Router, of which the settings was modified - 192.168.1.1)

## Enable IP Forwarding in your Linux Device

[Enable IP Forwarding in Pi](https://linuxconfig.org/how-to-turn-on-off-ip-forwarding-in-linux), so that every packet not destined for Pi, will be forwarded to upstream Gateway (which in this case, would be the Wifi Router in the Network, of which the settings was modified in the earlier step)

## ADD IP Table rules for Packet Forwarding and SNAT in Linux Device (Pi)

This is to make, all packets destined for internet will be going in/out through Linux Device's network interface, so that packets could be captured and analyzed.
You could add the below to a startup script like /etc/rc.local

    sudo /sbin/iptables -P FORWARD ACCEPT
    sudo /sbin/iptables --table nat -A POSTROUTING -s "192.168.1.0/24" -o eth0 -j MASQUERADE
  
 
Source Address NAT is necessary, so that response packets from Router (which are coming from Internet), will always go through Pi's Network interface, before reaching original source device, which initiated the internet traffic. If we omit, Source NAT, response packets will be directly delivered to the Original Device by the Router, bypassing Pi's Network Interface. Which makes the Bandwidth calculation out of sync.

If you've docker intalled in the Linux Device, docker will populate the IP tables by it's own by rewriting any custom rules placed. Putting the below in /etc/rc.local will circumvent these issues:

    while ! iptables -n --list DOCKER >/dev/null 2>&1
    do
        sleep 5;
    done
    sleep 10;

    sudo /sbin/iptables -P FORWARD ACCEPT
    sudo /sbin/iptables --table nat -A POSTROUTING -s "192.168.1.0/24" -o eth0 -j MASQUERADE
