import psutil

def get_active_interfaces():
    stats_awal = psutil.net_io_counters(pernic=True)
    interfaces = {}

    for iface, data in stats_awal.items():
        total_bytes = data.bytes_recv + data.bytes_sent
        interfaces[iface] = {
            "total": total_bytes,
            "recv": data.bytes_recv,
            "sent": data.bytes_sent
        }

    # Urutkan berdasarkan total aktivitas data
    interfaces_sorted = sorted(interfaces.items(), key=lambda x: x[1]["total"], reverse=True)
    return interfaces_sorted

for iface, data in get_active_interfaces():
    print(f"{iface}: Total={data['total']} bytes, RX={data['recv']}, TX={data['sent']}")
