from threading import Thread
import subprocess
import time
import usb
import os


class Printer:
    def __init__(self, printer_model, statistics):
        print(f"[PRINTER | MAIN] Printer process opened using printer:{printer_model}")
        if printer_model == '':
            self.printer_model = 'kp300v'
        else:
            self.printer_model = printer_model
        self.printer_communication_function = self.select_printer()
        self.statistics = statistics
        self.check_printer_process = Thread(target=self.checkPrinter)
        self.printer_status = 'Açılıyor...'
        self.level_code = 'yellow'
        self.check_printer_process.start()

    def checkPrinter(self):
        while True:
            try:
                printer_status, level_code = self.printer_communication_function()
                self.printer_status = printer_status
                self.level_code = level_code
            except Exception as e:
                print('-------------Version Control-------------')
                print(e)
                print('--------------------------')

            time.sleep(360)

    def select_printer(self):
        function_list = {
            "kp300v": self.printer_kp300v,
            "kp347": self.printer_kp347,
        }

        try:
            return function_list.get(self.printer_model, 0)

        except Exception as e:
            print("Error while selecting printer:", e)
            return 0

    def printout(self, button, file) -> bool:
        try:
            file_path = f"{os.getcwd()}/pdf/{str(button)}/{file}.pdf"
            subprocess.run(['cancel', '-a'])
            subprocess.run(["lp", "-o fit-to-page", file_path], capture_output=True)
            print(f'Starting printing process for document: /{button}/{file}')
            self.statistics.add_tap(f'BUTTON{str(button)}', file)
            return True
        except Exception as e:
            print('------------------ Printout Exception ------------------')
            print(e)
            print('--------------------------------------------------------')
            return False

    def change_printer_device(self, printer_model):
        self.printer_model = printer_model
        self.printer_communication_function = self.select_printer()

    def printer_kp300v(self):
        try:
            dev = usb.core.find(idVendor=0x0fe6, idProduct=0x811e)

            if not dev:
                return self.translate_status_code(-1)

            dev.reset()

            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)

            dev.set_configuration()

            EP_OUT = 0x03
            EP_IN = 0x81

            data = [0x1B, 0X76]
            dev.write(EP_OUT, data)

            response = dev.read(EP_IN, 8, timeout=10000)
            res_code = response[0]
            dev.reset()

            self.statistics.log_printer('kp300v', res_code)
            return self.translate_status_code(res_code)
        except Exception as e:
            print(f'[KP300V] {e}')
            return self.translate_status_code(-1)

    def printer_kp347(self):
        try:
            dev = usb.core.find(idVendor=0x0fe6, idProduct=0x811e)

            if not dev:
                return self.translate_status_code(0)

            dev.reset()

            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)

            dev.set_configuration()

            EP_OUT = 0x03
            EP_IN = 0x82

            data = [0x10, 0x04, 0x02]
            dev.write(EP_OUT, data)

            response = dev.read(EP_IN, 8, timeout=10000)
            res_code = response[0]
            dev.reset()

            self.statistics.log_printer('kp347', res_code)
            return self.translate_status_code(res_code)
        except Exception as e:
            print(e)
            return self.translate_status_code(0)

    def translate_status_code(self, code):
        try:
            translateCode = {
                "kp300v": {
                    "-1": ["Bi", "yellow"],
                    "0": ["Bi", "green"],
                    "4": ["Bi", "yellow"],
                },
                "kp347": {
                    "0": ["Bi", "yellow"],
                    "18": ["bi", "green"],
                    "114": ["bi", "yellow"],
                    "118": ["bi", "red"],
                }
            }

            if not translateCode[self.printer_model][str(code)][0]:
                return ["Bi", "yellow"]

            return [translateCode[self.printer_model][str(code)][0], translateCode[self.printer_model][str(code)][1]]
        except Exception as e:
            print("translate_status_code")
            print(e)
            return ["Bi", "yellow"]