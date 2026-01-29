import os
import subprocess

class Uad():
    def __init__(self, inst):
        self.inst = inst

    def reset(self):
        os.system(f'{self.inst}.exe com --action reset')

    def enable(self):
        os.system(f'{self.inst}.exe com --action enable')

    def disable(self):
        os.system(f'{self.inst}.exe com --action disable')

    def halt(self):
        csr = self.read_CSR()
        if csr is not None:
            csr |= (1 << 5)   # HALT
            csr |= (1 << 17)  # IBCLR: clear input buffer
            csr |= (1 << 18)  # TCLR: clear filter taps
            self.write_CSR(csr)

    def run(self):
        csr = self.read_CSR()
        if csr is not None:
            csr &= ~(1 << 5)  # HALT = 0
            csr |= 1          # FEN = 1
            self.write_CSR(csr)

    def read_CSR(self):
        try:
            output = os.popen(f'{self.inst}.exe cfg --address 0x0').read().strip()
            return int(output, 16)
        except:
            return None

    def write_CSR(self, value):
        os.system(f'{self.inst}.exe cfg --address 0x0 --data {hex(value)}')

    def read_COEF(self):
        try:
            output = os.popen(f'{self.inst}.exe cfg --address 0x4').read().strip()
            return int(output, 16)
        except:
            return None

    def write_COEF(self, value):
        os.system(f'{self.inst}.exe cfg --address 0x4 --data {hex(value)}')

    def write_signal(self, data):
        
        output = os.popen(f'{self.inst}.exe sig --data {hex(data)}').read().strip() # Use os.popen to capture output
        return int(output, 16) if output else None


def configure_coefficients(inst, config):
    print("\n--- Configuring Coefficients --", inst)
    test = Uad(inst)
    

    csr = test.read_CSR()  # Read current CSR
    print(f"Current CSR: 0x{csr:08X}")
    
    
    coef_reg = 0 # Build COEF register value
    
    for item in config:
        coef_num = item['coef']
        coef_value = item['value']
        en_value = item['en']
        
        bit_shift = coef_num * 8 # Add coefficient value to register
        coef_reg |= (coef_value << bit_shift)
        
        if en_value == 1: # Set/clear enable bit in CSR
            csr |= (1 << (coef_num + 1))
        else:
            csr &= ~(1 << (coef_num + 1))
        
        print(f"C{coef_num}: value=0x{coef_value:02X}, EN={en_value}")
    
    print(f"\nCOEF register value: 0x{coef_reg:08X}") # Write COEF register
    test.write_COEF(coef_reg)
    
    print(f"CSR value: 0x{csr:08X}")
    test.write_CSR(csr)
    
    print("Configuration complete!")


def drive_input_signals(inst, vector_file):
    print(f"\n--- Driving Input Signals from {vector_file} --", inst)
    test = Uad(inst)
    
    input_signals = []
    with open(vector_file, 'r') as file:
        for line in file:
            value = line.strip()
            if value:
                input_signals.append(int(value, 16))
    
    print(f"Loaded {len(input_signals)} input signals")
    
    print("\n--- Input/Output Results ---")
    print(f"{'Index':<6} {'Input':<10} {'Output':<10}")
    print("-" * 30)
    
    for i, data in enumerate(input_signals):
       
        output = test.write_signal(data)   # Write signal and capture output
        
        if output is not None:
            print(f"{i:<6} 0x{data:02X}       0x{output:02X}")
        else:
            print(f"{i:<6} 0x{data:02X}       READ FAILED")



config = [] # Read config file

with open('p0.cfg', 'r') as file:
    lines = file.readlines()
    
    for line in lines[1:]:
        parts = line.strip().split(',')
        config.append({
            'coef': int(parts[0]),
            'en': int(parts[1]),
            'value': int(parts[2], 16)
        })

print("="*40)
print("Config loaded from p0.cfg:")
print("="*40)
for item in config:
    print(f"coef={item['coef']}, en={item['en']}, value=0x{item['value']:02X}")

inst = "impl0"

print(f"\n{'='*40}")
print(f"Testing {inst}")
print(f"{'='*40}")

test = Uad(inst)

print("\nStep 1: Reset")
test.reset()

print("Step 2: Enable")
test.enable()

print("Step 3: Halt (for configuration)")
test.halt()

configure_coefficients(inst, config)

print("\nStep 4: Run (start filtering)")
test.run()

drive_input_signals(inst, 'sqr.vec')
