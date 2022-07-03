# openprog
Open Programmer for Microcontroller: 89S, AVR, Nuvoton, ...
![Schematic](hardware/Schematic_M252FC2AE.png?raw=true "Schematic")
Based on M252FC2AE from Nuvoton
1. Using a progammer as Nu-Link to burn bootloader.hex to M252FC2AE (to LDROM, option: boot from LDROM without IAP mode)
2. Hold Boot button, plug in the computer, release Boot button
3. Install driver
4. Open Terminal: firmware.py firmware/openprog.bin
5. Let go
![Atmega8](img/atmega8.png?raw=true "Atmega8")
# SPI connection: 89S, AVR...
1. PB13: MOSI
2. PB14: MISO
3. PB12: SCK
4. PF2: RESET
