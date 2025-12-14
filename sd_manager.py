import machine
import os

def mount_sd():
    print("Mounting SD Card...")
    
    # List of configs to try for SDMMC
    configs = [
        ("Default", {}),
        ("N16R8", {"clk": 39, "cmd": 38, "d0": 40}),
        ("Generic", {"clk": 14, "cmd": 15, "d0": 2}),
    ]

    for name, kwargs in configs:
        print(f"Trying SDMMC ({name})...")
        try:
            # Note: width=1 is standard for breakout boards
            sd = machine.SDCard(slot=1, width=1, **kwargs)
            os.mount(sd, "/sd")
            print(f"SD Mounted /sd (SDMMC {name})")
            return True
        except TypeError:
            print("  (Pin config not supported by this firmware)")
        except Exception as e:
            print(f"  Failed: {e}")

    # Fallback to SPI
    print("Trying SPI (SCK=12, MOSI=11, MISO=13)...")
    try:
        spi = machine.SPI(2, baudrate=1000000, polarity=0, phase=0, 
                          sck=machine.Pin(12), mosi=machine.Pin(11), miso=machine.Pin(13))
        
        # Extended CS list
        for cs_pin in [10, 34, 5, 4, 38, 13, 9]:
            try:
                print(f"Trying CS={cs_pin}...")
                sd = machine.SDCard(slot=2, width=1, spi=spi, cs=machine.Pin(cs_pin))
                os.mount(sd, "/sd")
                print(f"SD Mounted /sd (SPI CS={cs_pin})")
                return True
            except:
                pass
    except Exception as e:
        print(f"SPI Init failed: {e}")

    print("SD Card Mount Failed.")
    return False
