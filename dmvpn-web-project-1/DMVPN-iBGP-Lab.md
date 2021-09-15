# DMVPN lab setup based on this diagram. Keeping things simple, as the rabbit hole with IPSEC Profiles and BGP can go quite deep.
 - Using EVE-NG and some Cisco vIOS images. Any Virtual PC can be used as a test station within the environment.
 - The IP Addressing is not a best practice, but as for keeping the branches logically located within the RIB.
 - DMVPN will use Next-Hop Reslution Protocol to register the branches. iBGP will distribute the routing table.
 - The Central router ISP1 from the diagram is using static routing to interconnect the branches with main.  


![Lab Network](https://github.com/kevin-on-github/kevin-on-github.github.io/raw/main/images/post4_img_screenshot2.png)  

## Setup the devices starting with ISP1. We will assign static ip addresses to the gigabit interfaces, and bring up a loopback device to include in routing.

### ISP1:


        enable
        configure terminal
        hostname ISP1
        service timestamps debug datetime msec
        service timestamps log datetime msec
        interface GigabitEthernet0/0
         ip address 10.1.1.2 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
        !
        interface GigabitEthernet0/1
         ip address 20.1.1.2 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
        !
        interface GigabitEthernet0/2
         ip address 30.1.1.2 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
        !
        interface GigabitEthernet0/3
         ip address 40.1.1.2 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
        !
        interface range GigabitEthernet0/0-3
         no shut

### MAIN-10


        enable
        configure terminal
        hostname MAIN-10
        service timestamps debug datetime msec
        service timestamps log datetime msec
        !
        interface Loopback0
         description Loopback to simulate a local network
         ip address 10.10.10.10 255.255.255.255
        !
        interface GigabitEthernet0/0
         description Conn to ISP
         ip address 10.1.1.1 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
         no shutdown
        ! Static route added to establish public connectivity to the ISP
        ip route 0.0.0.0 0.0.0.0 10.1.1.2

### BRANCH-20


        enable
        configure terminal
        hostname BRANCH-20
        service timestamps debug datetime msec
        service timestamps log datetime msec
        !
        interface Loopback0
         description Loopback
         ip address 20.20.20.20 255.255.255.255
        !
        interface GigabitEthernet0/0
         description Conn to ISP
         ip address 20.1.1.1 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
         no shutdown
        interface GigabitEthernet0/1
         description Local network for Branch-20
         ip address 20.1.20.20 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
         no shutdown
        ! Add a static route for public access
        ip route 0.0.0.0 0.0.0.0 20.1.1.2

### BRANCH-30


        enable  
        configure terminal  
        hostname BRANCH-30  
        service timestamps debug datetime msec  
        service timestamps log datetime msec  
        !  
        interface Loopback0  
         description Loopback  
         ip address 30.30.30.30 255.255.255.255  
        !  
        interface GigabitEthernet0/0  
         description Conn to ISP  
         ip address 30.1.1.1 255.255.255.0  
         duplex auto  
         speed auto  
         media-type rj45  
         no shutdown  
        !  
        interface GigabitEthernet0/1  
         description Local network for Branch-30  
         ip address 30.1.30.30 255.255.255.0  
         duplex auto  
         speed auto  
         media-type rj45  
         no shutdown  
        ! Add a static route for public access
        ip route 0.0.0.0 0.0.0.0 30.1.1.2
### BRANCH-40


        enable
        configure terminal
        hostname BRANCH-40
        service timestamps debug datetime msec
        service timestamps log datetime msec
        !
        interface Loopback0
         description Loopback
         ip address 40.40.40.40 255.255.255.255
        !
        interface GigabitEthernet0/0
         description Conn to ISP
         ip address 40.1.1.1 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
        !
        interface GigabitEthernet0/1
         description Local network for Branch-40
         ip address 40.1.40.40 255.255.255.0
         duplex auto
         speed auto
         media-type rj45
        ! Add a static route for public access
        ip route 0.0.0.0 0.0.0.0 40.1.1.2


### Define a crypto Keyring, IKEv2 profile, and Transform set to make the IPSEC Profile.
  - Will apply this IPSEC profile to the GRE Tunnel interface of main and the branches.


        crypto ikev2 keyring IKEV2_KR
         peer ANYv4
         address 0.0.0.0 0.0.0.0
         pre-shared-key cisco123
        !
        crypto ikev2 profile IKEV2_PROF
         match identity remote address 0.0.0.0 
         identity local address 10.10.10.10
         authentication remote pre-share
         authentication local pre-share
         keyring local IKEV2_KR
        ! There are transform sets built in, so rarely is it necessary to create from scratch
        crypto ipsec transform-set IPSEC_TRANS esp-aes 256 esp-sha256-hmac 
         mode transport
        crypto ipsec profile IPSEC_PROF
         set transform-set IPSEC_TRANS 
         set ikev2-profile IKEV2_PROF
        ! Limit the number of SA connection attempts as a basic DDoS protection mechanism.
        crypto ikev2 limit max-in-negotation-sa 8 outgoing
        crypto ikev2 limit max-in-negotation-sa 8
        crypto ikev2 limit max-sa 10
        crypto ikev2 cookie-challenge 4
 

### Now we can establish the multipoint GRE connections. 
 - The ease here is that the branch setup is essentially a template that can be quickly deployed.
 - NOTE: Because GRE uses ~40 bytes of the header, this can cause fragmentation and connectivity issues. To resolve this there are some MTU and TCP adjustments included in the config. In a lab it isn't necessary, but it's good to remember.

### Main office router


        interface Tunnel0
         bandwidth 1000000
         ip address 172.16.1.1 255.255.255.0
         ip mtu 1400
         ip nhrp network-id 100
         ! nhrp redirect is important here as it specifies this as a phase 3 hub
         ip nhrp redirect
         ip tcp adjust-mss 1360
         ip ospf network point-to-multipoint
         tunnel source GigabitEthernet0/0
         tunnel mode gre multipoint
         tunnel key 100
         ! This isn't built yet, but will come back to it. This encrypts the traffic inside the tunnel.
         tunnel protection ipsec profile IPSEC_PROF


### Branch office routers


        interface Tunnel0
         bandwidth 1000000
         !Specify a unique ip address for the tunnel interface. X = .1 is main, .2 is branch-20, etc.
         ip address 172.16.1.{X} 255.255.255.0
         ip mtu 1400
         ip nhrp network-id 100
         ! nhrp shortcut is important here as it specifies this as a phase 3 spoke
         ip nhrp shortcut
         ! Here modify the non-broadcast multi-access address to the public ip address of each branch router.
         ip nhrp nhs 172.16.1.1 nbma {X}.1.1.1 multicast
         ip tcp adjust-mss 1360
         tunnel source GigabitEthernet0/0
         tunnel mode gre multipoint
         tunnel key 100
         ! This isn't built yet, but will come back to it. This encrypts the traffic inside the tunnel.
         tunnel protection ipsec profile IPSEC_PROF
 
### iBGP is a fairly quick setup. Sure there are more complicated and fancy ways to do this, but as a quick lab, here we go.
 - We will establish all neighborships from Main to the branches with the route-reflector so that iBGP routes can be distributed. This is how iBGP functions. The other method involves using next-hop-self, but I find route-reflectors work just fine.

 ### Main BGP Setup


        router bgp 65000
         bgp log-neighbor-changes
         no bgp default ipv4-unicast
         neighbor 172.16.1.2 remote-as 65000
         neighbor 172.16.1.3 remote-as 65000
         neighbor 172.16.1.4 remote-as 65000
        !
         address-family ipv4
          network 10.10.10.10 mask 255.255.255.255
          network 172.16.1.0 mask 255.255.255.0
          neighbor 172.16.1.2 activate
          neighbor 172.16.1.2 route-reflector-client
          neighbor 172.16.1.3 activate
          neighbor 172.16.1.3 route-reflector-client
          neighbor 172.16.1.4 activate
          neighbor 172.16.1.4 route-reflector-client
         exit-address-family

### Branch BGP Setup
 - Make sure to edit the network statement to inject the correct routing tables.


        router bgp 65000
         bgp log-neighbor-changes
         no bgp default ipv4-unicast
         neighbor 172.16.1.1 remote-as 65000
         !
         address-family ipv4
          network X.X.X.X mask 255.255.255.0
          network X.X.X.X mask 255.255.255.255
          neighbor 172.16.1.1 activate
         exit-address-family

### At this stage the DMVPN w IPSEC and iBGP is up and running.
 - Determine status of the DMVPN tunnels.


        Main10#sho dmvpn ipv4 detail | begin Interface
          Interface Tunnel0 is up/up, Addr. is 172.16.1.1, VRF "" 
          Tunnel Src./Dest. addr: 10.1.1.1/Multipoint, Tunnel VRF ""
          Protocol/Transport: "multi-GRE/IP", Protect "IPSEC_PROF" 
          Interface State Control: Disabled
          nhrp event-publisher : Disabled
        Type:Hub, Total NBMA Peers (v4/v6): 3

        # Ent  Peer NBMA Addr Peer Tunnel Add State  UpDn Tm Attrb    Target Network
        ----- --------------- --------------- ----- -------- ----- -----------------
            1 20.1.1.1             172.16.1.2    UP 00:14:12     D      172.16.1.2/32
            1 30.1.1.1             172.16.1.3    UP 00:14:15     D      172.16.1.3/32
            1 40.1.1.1             172.16.1.4    UP 00:14:15     D      172.16.1.4/32


        Crypto Session Details: 
        --------------------------------------------------------------------------------

        Interface: Tunnel0
        Session: [0x1142B350]
        Session ID: 14  
        IKEv2 SA: local 10.1.1.1/500 remote 20.1.1.1/500 Active 
                Capabilities:(none) connid:2 lifetime:23:45:48
        Crypto Session Status: UP-ACTIVE     
        fvrf: (none),	Phase1_id: 20.20.20.20
        IPSEC FLOW: permit 47 host 10.1.1.1 host 20.1.1.1 
                Active SAs: 2, origin: crypto map
                Inbound:  #pkts dec'ed 41 drop 0 life (KB/Sec) 4363006/2747
                Outbound: #pkts enc'ed 42 drop 0 life (KB/Sec) 4363006/2747
        Outbound SPI : 0x4535C3E2, transform : esp-256-aes esp-sha256-hmac 
            Socket State: Open

        Interface: Tunnel0
        Session: [0x1142B258]
        Session ID: 12  
        IKEv2 SA: local 10.1.1.1/500 remote 30.1.1.1/500 Active 
                Capabilities:(none) connid:1 lifetime:23:45:44
        Crypto Session Status: UP-ACTIVE     
        fvrf: (none),	Phase1_id: 30.30.30.30
        IPSEC FLOW: permit 47 host 10.1.1.1 host 30.1.1.1 
                Active SAs: 2, origin: crypto map
                Inbound:  #pkts dec'ed 38 drop 0 life (KB/Sec) 4321173/2744
                Outbound: #pkts enc'ed 38 drop 0 life (KB/Sec) 4321173/2744
        Outbound SPI : 0x6E58853D, transform : esp-256-aes esp-sha256-hmac 
            Socket State: Open

        Interface: Tunnel0
        Session: [0x1142B448]
        Session ID: 13  
        IKEv2 SA: local 10.1.1.1/500 remote 40.1.1.1/500 Active 
                Capabilities:(none) connid:3 lifetime:23:45:44
        Crypto Session Status: UP-ACTIVE     
        fvrf: (none),	Phase1_id: 40.40.40.40
        IPSEC FLOW: permit 47 host 10.1.1.1 host 40.1.1.1 
                Active SAs: 2, origin: crypto map
                Inbound:  #pkts dec'ed 40 drop 0 life (KB/Sec) 4292426/2744
                Outbound: #pkts enc'ed 40 drop 0 life (KB/Sec) 4292426/2744
        Outbound SPI : 0x19CD2CE4, transform : esp-256-aes esp-sha256-hmac 
            Socket State: Open

        Pending DMVPN Sessions:
 
 - Determine status of the IPSEC Security Associations


        Main10#sho crypto ikev2 sa
        IPv4 Crypto IKEv2  SA 

        Tunnel-id Local                 Remote                fvrf/ivrf            Status 
        2         10.1.1.1/500          20.1.1.1/500          none/none            READY  
            Encr: AES-CBC, keysize: 256, PRF: SHA512, Hash: SHA512, DH Grp:5, Auth sign: PSK, Auth verify: PSK
            Life/Active Time: 86400/1161 sec

        Tunnel-id Local                 Remote                fvrf/ivrf            Status 
        1         10.1.1.1/500          30.1.1.1/500          none/none            READY  
            Encr: AES-CBC, keysize: 256, PRF: SHA512, Hash: SHA512, DH Grp:5, Auth sign: PSK, Auth verify: PSK
            Life/Active Time: 86400/1165 sec

        Tunnel-id Local                 Remote                fvrf/ivrf            Status 
        3         10.1.1.1/500          40.1.1.1/500          none/none            READY  
            Encr: AES-CBC, keysize: 256, PRF: SHA512, Hash: SHA512, DH Grp:5, Auth sign: PSK, Auth verify: PSK
            Life/Active Time: 86400/1165 sec

        IPv6 Crypto IKEv2  SA 

 - Verify that iBGP routes are working.


        Main10#show ip bgp ipv4 unicast summary
        BGP router identifier 10.10.10.10, local AS number 65000
        BGP table version is 15, main routing table version 15
        8 network entries using 1152 bytes of memory
        8 path entries using 672 bytes of memory
        2/2 BGP path/bestpath attribute entries using 320 bytes of memory
        0 BGP route-map cache entries using 0 bytes of memory
        0 BGP filter-list cache entries using 0 bytes of memory
        BGP using 2144 total bytes of memory
        BGP activity 8/0 prefixes, 11/3 paths, scan interval 60 secs

        Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
        172.16.1.2      4        65000     305     308       15    0    0 04:33:35        2
        172.16.1.3      4        65000     301     310       15    0    0 04:31:10        2
        172.16.1.4      4        65000     303     307       15    0    0 04:30:42        2

 - And lets see what those network and next-hop routes look like in the topology


        Main10#sho ip bgp ipv4 unicast topo *
        For address family: IPv4 Unicast

        BGP table version is 15, local router ID is 10.10.10.10
        Status codes: s suppressed, d damped, h history, * valid, > best, i - internal, 
                    r RIB-failure, S Stale, m multipath, b backup-path, f RT-Filter, 
                    x best-external, a additional-path, c RIB-compressed, 
                    t secondary path, 
        Origin codes: i - IGP, e - EGP, ? - incomplete
        RPKI validation codes: V valid, I invalid, N Not found

            Network          Next Hop            Metric LocPrf Weight Path
        *>   10.10.10.10/32   0.0.0.0                  0         32768 i
        *>i  20.1.20.0/24     172.16.1.2               0    100      0 i
        *>i  20.20.20.20/32   172.16.1.2               0    100      0 i
        *>i  30.1.30.0/24     172.16.1.3               0    100      0 i
        *>i  30.30.30.30/32   172.16.1.3               0    100      0 i
        *>i  40.1.40.0/24     172.16.1.4               0    100      0 i
        *>i  40.40.40.40/32   172.16.1.4               0    100      0 i
        *>   172.16.1.0/24    0.0.0.0                  0         32768 i

### Now from a virtual machine in the environment we can verify communication between the branches and main office.
 
 - Enable shell functions to allow scripting on IOS
 

        enable
        configure terminal
        shell processing full
 
 - Iterate through a list of IPs to verify connectivity.


        main# for ip in '10.10.10.10' '20.20.20.20' '30.30.30.30' '40.40.40.40'; do ping ip $ip repeat 1 source loop0; done
        
        Type escape sequence to abort.
        Sending 1, 100-byte ICMP Echos to 10.10.10.10, timeout is 2 seconds:
        Packet sent with a source address of 10.10.10.10 
        !
        Success rate is 100 percent (1/1), round-trip min/avg/max = 1/1/1 ms
        Type escape sequence to abort.
        Sending 1, 100-byte ICMP Echos to 20.20.20.20, timeout is 2 seconds:
        Packet sent with a source address of 10.10.10.10 
        !
        Success rate is 100 percent (1/1), round-trip min/avg/max = 8/8/8 ms
        Type escape sequence to abort.
        Sending 1, 100-byte ICMP Echos to 30.30.30.30, timeout is 2 seconds:
        Packet sent with a source address of 10.10.10.10 
        !
        Success rate is 100 percent (1/1), round-trip min/avg/max = 10/10/10 ms
        Type escape sequence to abort.
        Sending 1, 100-byte ICMP Echos to 40.40.40.40, timeout is 2 seconds:
        Packet sent with a source address of 10.10.10.10 

### This concludes the DMVPN lab.