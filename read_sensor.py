import time
from pymodbus.client import ModbusSerialClient

# Configure the RS485 connection
client = ModbusSerialClient(
    port='/dev/ttyUSB0',
    baudrate=4800,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=2
)

def read_sensor():
    if client.connect():
        print("Connected! Reading data (Press Ctrl+C to stop)...")
        try:
            while True:
                # pymodbus 3.12.1 uses device_id for the Modbus RTU unit address
                result = client.read_holding_registers(address=0x0000, count=2, device_id=1)
                
                if not result.isError():
                    # Turbidity is register 0, Temperature is register 1
                    # Both are enlarged 10x
                    turbidity = result.registers[0] / 10.0
                    temperature = result.registers[1] / 10.0
                    print(f"Turbidity: {turbidity:0.1f} NTU | Temperature: {temperature:0.1f} °C")
                else:
                    print(f"Modbus Error: {result}")
                
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopped reading.")
        finally:
            client.close()
    else:
        print("Failed to open the USB port. Check your connection or permissions.")

if __name__ == "__main__":
    read_sensor()