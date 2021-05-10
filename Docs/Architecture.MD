## WhiteStat require Linux Device to be the Default Gateway for the Network
[See configuration](https://github.com/avarghesein/WhiteStat/blob/main/Docs/LinuxDeviceAsGateway.md)


## WhiteStat Roles

WhiteStat, has two roles;

### 1. As Monitor

Using this role, Whitestat captures network packets from the host network interfaces for analysis by "Analyzer Role". This role has designed to be lean, so that it could be run smoothly on the Gateway Device without much overhead

### 2. As Analyzer

Analyzer Role, will process the captured packes to generate Daily Network Usage report. This is resource intensive compared to "Monitor" role.

## Deployment models

By default WhiteStat, will run both "Monitor" and "Analyzer" roles in a single container, as it is the easiest setup.
Below figure shows this setup.

![alt arch](https://github.com/avarghesein/WhiteStat/blob/main/Docs/WhiteStatMultiRolePerDevice.png)

However, if the Gateway Device is less in system resources, it is recommended to run the “Analyzer” role as a separate container in another host with enough resources. This will also make the Gateway Device smooth in operation as well. Below diagram depicts this configuration

![alt arch](https://github.com/avarghesein/WhiteStat/blob/main/Docs/WhiteStatRolePerDevice.png)


## Detailed Technical Architecture

![alt tech arch](https://github.com/avarghesein/WhiteStat/blob/main/Docs/WhiteStatArch.png)
