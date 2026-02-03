from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand


class DummyDevice:
    pass


def test_parse_interface_info_basic():
    output = (
        "p2p0      Link encap:Ethernet  HWaddr 02:79:55:67:b6:1b\n"
        "          inet addr:192.168.49.20  Bcast:192.168.49.255  Mask:255.255.255.0\n"
        "          inet6 addr: fe80::c79:55ff:fe67:b61b/64 Scope:Link\n"
        "          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1\n"
    )
    cmd = NetworkInterfaceCommand(DummyDevice(), interface="p2p0")
    result = cmd.parse_interface_info(output)

    assert result["ipv4"] == "192.168.49.20"
    assert result["ipv6"].startswith("fe80::")
    assert result["status"] == "UP"
    assert "RUNNING" in result["flags"]
    assert result["mtu"] == "1500"
    assert result["metric"] == "1"
