# openprog
Open Programmer for Microcontroller: 89S, AVR, Nuvoton, ...
![Alt text](hardware/Schematic_M252FC2AE.png?raw=true "Schematic")
Based on M252FC2AE from Nuvoton
1. Using a progammer as Nu-Link to burn bootloader.hex to M252FC2AE
2. Hold Boot button, plug in the computer, release Boot button
3. Install driver
4. Open Terminal: firmware.py firmware/openprog.bin
5. Let go
![Alt text](img/atmega8.png?raw=true "Atmega8")
# SPI connection: 89S, AVR...
PB13: MOSI
PB14: MISO
PB12: SCK
PF2: RESET
