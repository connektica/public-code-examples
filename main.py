from public_code_examples.drivers.znb import VNA, VNAConfig


ZNB_ADDR = "TCPIP::192.168.29.103::5025::SOCKET" # EDIT ME


def main():
    """
    Instantiating VNA instrument and fetching data
    """
    vna = VNA(connection_string=ZNB_ADDR, config=VNAConfig())
    print(vna.query("*IDN?"))
    
    temp = vna.get_traces(("Trc1",), data_format="db-phase")
    print(temp)


if __name__ == "__main__":
    main()