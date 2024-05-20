import serial
import time
from multiprocessing import Process, Queue


def serial_process(serial_port, baud_rate, qstdout, qstdin):
    try:
        with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
            print(f"Serial port {serial_port} opened at {baud_rate} bps.")

            while True:
                if not qstdout.empty():
                    message = qstdout.get_nowait()
                    ser.write(message.encode())
                    print(f"Sent: {message}")

                if ser.in_waiting > 0:
                    incoming_data = ser.readline().decode("utf-8").strip()
                    qstdin.put(incoming_data)
                    print(f"Received: {incoming_data}")

                time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Serial connection closed.")


def main():
    serial_port = "/dev/ttyGS0"
    baud_rate = 9600

    qstdout = Queue()
    qstdin = Queue()

    serial_thread = Process(target=serial_process, args=(serial_port, baud_rate, qstdout, qstdin))
    serial_thread.start()

    try:
        qstdout.put("Hello from Linux")
        while True:
            time.sleep(0.1)
            while not qstdin.empty():
                print(f"Main received: {qstdin.get()}")

    except KeyboardInterrupt:
        print("Stopping serial communication.")

    finally:
        serial_thread.terminate()
        serial_thread.join()
        print("Process terminated.")


if __name__ == "__main__":
    main()
