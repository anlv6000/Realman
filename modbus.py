# modbus.py

from pymodbus.client.sync import ModbusSerialClient
from time import sleep
import threading

lock = threading.Lock()
class PLCStation:
    def __init__(self, serial_port, baudrate, timeout):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout

        self.client = ModbusSerialClient(
            method='rtu',
            port=self.serial_port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            bytesize=8,
            stopbits=1,
            parity="N"
        )
        self.client.connect()

    

    def read_datas_input(self, slave_id: int, count: int) -> list[int]:
        cnt = 0
        while cnt < 3:
            with lock:
                res = self.client.read_discrete_inputs(0, count, unit=slave_id)
                if not res.isError():
                    return list(res.bits)[:count]
                else:
                    cnt += 1
                    sleep(0.2)
                if cnt == 3:
                    print(f"Give up sending to PLC: {slave_id}")
                    return [False] * count
                    
    
    def write_datas_output(self, slave_id: int, values: list[bool]) -> bool:
        cnt = 0
        while cnt < 3:
            with lock:
                res = self.client.write_coils(0, values= values, unit=slave_id)
                if not res.isError():
                    return True
                else:
                    cnt += 1
                    sleep(0.2)
                if cnt == 3:
                    print(f"Give up sending to PLC: {slave_id}")
                    return False


# if __name__ == "__main__":
#     print("Starting PLC communication...")
#     try:
#         comiunity_PLC = PLCStation(serial_port= "COM5", baudrate= 9600, timeout= 1)
#         while True:
#             data = comiunity_PLC.read_datas_input(slave_id= 254, count= 5)
#             if data[0] is True:
#                 comiunity_PLC.write_datas_output(slave_id= 254, values= [False, True, False, False, False])
#             else:
#                 comiunity_PLC.write_datas_output(slave_id= 254, values= [False, False, False, False, False])
#             print(data)
#             sleep(0.5)
#     except KeyboardInterrupt:
#         print("Exiting...")