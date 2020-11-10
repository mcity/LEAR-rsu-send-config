# Lear Roadstar RSU BSM offload and BSM/PSM/SRM/SSM immediate forward
The following configurations enable support for a LEAR Roadstar RSU to forward all received DSRC BSMs to a 3rd party server over UDP and enable immediate forwarding of UDP sent message to DSRC J2735_2016 clients.

Configuration changes are made through the command line interface after SSH-ing as admin to the RSU. You'll need both the user password (SSH and viewing configurations) and the admin password (enable and request RSU commands)

## Port standards
For the purpose of these examples we do not use the SAE standard UDP port 1516 to provide this functionality. Ports used are below.

62491 - Receive 2016 DSRC Message Frames (BSM/PSM...)
62450 - RSU receives BSM for immediate forward here.
62451 - RSU receives PSM for immediate forward here.
1516 - DEFAULT
1517 -  RSU receives SSM for immediate forward here.
1518 - RSU receives SRM for immediate forward here.

## BSM Offload
Configure the RSU to forward received BSMs.

SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```
Provide the non-admin password here and enter the LEAR CLI. The Lear CLI auto completes commands and is particularly picky about copy and paste efforts. For changes outside of the request shell, it's recommended to tab complete and manually type the commands. Failure to do so results in additional characters being entered into the custom app configurations while in enable/configure mode.

View existing custom application configurations and find a free/available custom application slot.
```sh
show application details
```

Results in the final lines showing which custom application slots are available/in use on the RSU.
```
app_name 	=>	 customapp1
app_status 	=>	 disabled
app1_Name 	=>	 NA
app1_arg 	=>	 NA
```

We see that customapp1 is free. If you wish to reuse an in use custom application slot, first disable the application, before making changes. For all changes the user must be in enable/config mode. 

```sh
enable
```
Enter the admin/super user password here.

Knowing that custom app 1 is available, configure the RSU to send BSMs (or any other message) to a specific IP and port.
```
config
config customApp disable app1
```

With the application disabled, we can now configure the BSM offload to a 3rd party server. The Lear RSU uses an application named wsmpforward to send data to a different IP address (141.X.X.x). Below is a sample command line for configuration. We'll break down the parameters afterward.

```
config customApp update app1 /usr/local/bin/wsmpforward "32 141.X.X.X 62491 0 0 172 2 3"
```

* /usr/local/bin/wsmpforward - This is the application that will be run and in this case will listen to all received DSRC messages and forward those that match the requested requirements.
* 32 - The PSID (provider service identifier) for the application of the message. See IEEE/DSRC standards for listing. Common message PSID's are BSM (32), MAP (130), PDM (132), PVD(132), SPAT (130), TIM (131)
* 141.X.X.X - A sample server IP address for the receiving server.
* 62491 - The remote server UDP port to transmit packets to.
* 0 - The first 0 shown in the example is if to send the plain (1) payload or the (0) dot 2 payload. During testing it appeared that for RSUs where security/certs were disabled (but still broadcast by the OBU) that setting 0 was required. Setting 1 here for plain payload caused the RSU to attempt to decode the dot2 header and on failure (as it was all null) the RSU would not forward the packet.
* 0 - Represents if the RSU should attempt to decode the WSMP header (dot1 and dot2). We sent to 0 as without security enabled, but still sending the dot2, this would cause the RSU to fail the decode and not forward the data. 1 is enable decode, 0 is disabled.
* 172 - Represents the channel that data being listened for should forward on. Our RSUs specifically are set to listen for BSMs on channel 172 in our environment.
* 2 - Forwarding message type BSM (2), MAP(6), PDM (9), PVD(10), SPAT(13), TIM (16)
* 3 - Should the RSU only forward alternating or continuously sent messages. Alternating messages allow for picking the first part or the second portion of the broadcast time on the channel. Options are 1 or 2 for the alternating broadcast (PSM, MAP etc...) or 3 for continuously broadcasted messages (SPAT/BSM etc...)
* Unspecified optional parameter for printing the decoded message. If decoding is enabled and running the wsmp forward application from the command line (request shell) then this application can be sent to print the decoded message payload to the command line. Specify 1 as the final parameter to enable the print or 0 to disable the print.

Modifications on this command can be made to enable forwarding of other types of messages.

Enable the custom application

```sh
config customApp enable app1
```

Exit configuration mode.
```sh
exit
```

View the saved configuration of the running application
```sh
show application details
```

### SRM Offload
If this path is already used for another forwarding, be sure to use a new symlink to wsmpforward such as /var/wsmpforward_SRM.

```sh
config customApp update app3 /usr/local/bin/wsmpforward "2113686 10.224.50.144 62450 0 0 176 29 2"
config customAPP enable app3
```

### Command line debug of wsmp forward.
The wsmp forward application provides information to standard out when run and can optionally be enabled to print a decoded wsmp/dot2 message to the command line. To enable this the user must connect to the RSU and enter a shell before running the wsmp forward command manually. On disconnect this application will cease to run.

SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
request
```
Enter the admin user password

Request a shell
```sh
request system shell
```

Run the desired command on the command line to view std out. Ctrl-c to kill it.
```sh
/usr/local/bin/wsmpforward 32 141.X.X.X 62491 0 0 172 2 3
```

Exit to LEAR CLI
```sh
exit
```

### Running two copies
If you wish to run two instances of wsmpforward, the application must be called using a symbolic link from the custom app configuration. You cannot run two applications with the same command line path. The Lear RSU will not error, it will not fail, it just will silently not forward messages for any of your configured applications. 

Also to note that two applications with the same command line path, one enabled and one disabled, will also cause the enabled custom app to not run/fail.

## Immediate forward application. 
The Lear RSU immediate forward application can be set up to receive a pre-encoded message payload on a specific UDP port and forward it to all listening DSRC clients. The configuration requires the incoming message to be sent in the SAE file format (a sample is included) and the parameters in the transmitted packet, must exactly match the configured parameters for the message to be valid for transmission

### Open firewall ports.
SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
enable
```
Enter the admin user password

Configure a firewall rule to allow traffic on UDP ports you'll send.
```sh
config firewall rule allow incoming port udp 62451
config firewall rule allow incoming port tcp 62451
config firewall rule allow incoming port tcp 1516
config firewall rule allow incoming port tcp 1517
config firewall rule allow incoming port tcp 1518
config firewall rule allow incoming port udp 1516
config firewall rule allow incoming port udp 1517
config firewall rule allow incoming port udp 1518
```
The documentation states to open the TCP port, but it shouldn't be necessary as the packet is flowing over UDP only inbound and the immediate forward app only appears to listen on UDP.

### Running two copies
If you wish to run two instances of immediate forward, the application must be called using a symbolic link from the custom app configuration. You cannot run two applications with the same command line path. The Lear RSU will not error, it will not fail, it just will silently not forward messages for any of your configured applications. 

Also to note that two applications with the same command line path, one enabled and one disabled, will also cause the enabled custom app to not run/fail.

If you'd like to receive and forward two types of messages, create a symbolic link as stated below and use that for your application path.

Example (from system request shell)
```sh
ln -s /usr/local/bin/immediateForwardMsg /var/immediateForwardMsg_BSM
ln -s /usr/local/bin/immediateForwardMsg /var/immediateForwardMsg_PSM
ln -s /usr/local/bin/immediateForwardMsg /var/immediateForwardMsg_SSM
```

### PSM Configuration Files
3 Files need to be placed in the right locations on the RSU. 
The filename format is:
* ifm_appname.conf -> /var/IFM/
* appname.conf -> /var/
* appnameOpt.conf -> /var/

Place the following files for PSM forwarding.
* ifm_opsm.conf -> var/IFM/ (644 admin:admin)
* opsm.conf -> /var/ (644 admin:admin)
* opsmOpt.conf -> /var/ (644 admin:admin)

It's important that the naming scheme here matches. The /var file is picked based on the names from the appname from the /var/ conf files.

SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
request
```
Enter admin password

Request a shell
```sh
request system shell
```

Either use vi or scp to get the files to the system and ensure their permissions are correct.

### BSM Configuration Files
3 Files need to be placed in the right locations on the RSU. 
The filename format is:
* ifm_appname.conf -> /var/IFM/
* appname.conf -> /var/
* appnameOpt.conf -> /var/

Place the following files for PSM forwarding.
* ifm_obsm.conf -> var/IFM/ (644 admin:admin)
* obsm.conf -> /var/ (644 admin:admin)
* obsmOpt.conf -> /var/ (644 admin:admin)

It's important that the naming scheme here matches. The /var file is picked based on the names from the appname from the /var/ conf files.

SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
request
```
Enter admin password

Request a shell
```sh
request system shell
```

Either use vi or scp to get the files to the system and ensure their permissions are correct.


### SSM Configuration Files
3 Files need to be placed in the right locations on the RSU. 
The filename format is:
* ifm_appname.conf -> /var/IFM/
* appname.conf -> /var/
* appnameOpt.conf -> /var/

Place the following files for PSM forwarding.
* ifm_ossm.conf -> var/IFM/ (644 admin:admin)
* ossm.conf -> /var/ (644 admin:admin)
* ossmOpt.conf -> /var/ (644 admin:admin)

It's important that the naming scheme here matches. The /var file is picked based on the names from the appname from the /var/ conf files.

SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
request
```
Enter admin password

Request a shell
```sh
request system shell
```

Either use vi or scp to get the files to the system and ensure their permissions are correct.

### SRM Configuration Files
3 Files need to be placed in the right locations on the RSU. 
The filename format is:
* ifm_appname.conf -> /var/IFM/
* appname.conf -> /var/
* appnameOpt.conf -> /var/

Place the following files for PSM forwarding.
* ifm_osrm.conf -> var/IFM/ (644 admin:admin)
* osrm.conf -> /var/ (644 admin:admin)
* osrmOpt.conf -> /var/ (644 admin:admin)

It's important that the naming scheme here matches. The /var file is picked based on the names from the appname from the /var/ conf files.

SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
request
```
Enter admin password

Request a shell
```sh
request system shell
```

Either use vi or scp to get the files to the system and ensure their permissions are correct.

### Changes to configuration files.
The settings in the .conf file need to match the channel, timeslot, psid and message type from the SAE format message you send or the message will not forward. Important fields here are serviceChannel, timeSlot, txChannel, TxMode, and TxChannel.

The udp port is set in the Opt.conf file.

The app config file contains the provider service identifier of the application that we are going to use. You can provide this value as hex or decimal (0x27 vs 39)


### Debugging a PSM/BSM custom forward application
SSH to RSU (10.X.x.x)
```sh
ssh admin@10.X.x.x
```

Enter request mode
```sh
request
```
Enter the admin user password

Request a shell
```sh
request system shell
```

Start the custom configuration for the immediate forward application. On receive of message standard output will display to confirm it's processed it.
```sh
immediateForwardMsg /var/opsm.conf /var/opsmOpt.conf
```

### Send a sample PSM via UDP.
Included is a sample python script that will transmit a UDP packet to the PSM configuration on the RSU for testing. The payload is in DSRC 2016 UPER encoded message frame format.
```sh
python3 test_sae_to_rsu.py
```

### Enabling a PSM/BSM custom immediate forward application
```sh
show application details
```

Results in the final lines showing which custom application slots are available/in use on the RSU.
```
app_name 	=>	 customapp1
app_status 	=>	 disabled
app1_Name 	=>	 NA
app1_arg 	=>	 NA
```

We see that customapp1 is free. If you wish to reuse an in use custom application slot, first disable the application, before making changes. For all changes the user must be in enable/config mode. 

```sh
enable
```
Enter the admin/super user password here.

Knowing that custom app 1 is available, configure the RSU to send BSMs (or any other message) to a specific IP and port.
```
config
config customApp disable app1
```

With the application disabled, we can now configure the immediate forward application. If you want to setup two instances, they will require a symbolic link so the application path is different or your configuration will just not work, but not error. 

```
config customApp update app1 /usr/local/bin/immediateForwardMsg "/var/opsm.conf /var/opsmOpt.conf"
```

Enable the custom application
```sh
config customApp enable app1
```

Exit configuration mode.
```sh
exit
```

View the saved configuration of the running application
```sh
show application details
```
