# Oneline's Hackpad
This a Hackpad that I have been working on for sometime for studying, video editing, gaming and voice chat. 

Renders:
<img width="1520" height="770" alt="f99d0113-4bce-4061-9304-6c1de86bcdb5" src="https://github.com/user-attachments/assets/9a97245d-ea52-46f1-8425-adfa00bc208b" />
<img width="1520" height="770" alt="Final_2026-Jan-10_11-23-39PM-000_CustomizedView1600068612" src="https://github.com/user-attachments/assets/b7e77d75-537f-4c24-9e3e-d19ff32e7654" />

## Features
- 6 Key Marcopad
  - Can Switch to diffrent layouts for diffrent task
* OLED screen for diffent modes and animations
+ LEDs for color and checking for power.

## Specifications
BOM:
- 1x Seeed XIAO RP2040 (SMD Mounted)
- 6x Cherry MX Switches
- 2x SK6812 MINI Leds
- 1x 0.91 inch OLED display
- 6x Blank DSA Keycaps
- 4x M3x16mm screws
- 4x M3 Heatset

Tools:
- 3D Printer
- Soldering Iron

Custom Parts
- 1x Back Case
- 1x Front Case
- 1x PCB

## CAD Model
> [!NOTE]
> This is my first time using Fusion. I used to using OnShape but Fusion was great experience to learn and use!
<img width="1021" height="719" alt="{8461DDD0-4026-43F3-8BD6-9767489A591B}" src="https://github.com/user-attachments/assets/c94836bf-5f80-415c-9b54-45088d249ef3" />

## PCB and Wiring
> [!NOTE]
> Same thing as the Fusion, make my first PCB was a challenge! After watching many videos and websites, I was able to get this working

> [!IMPORTANT]
> DRC was run and all tests have been passed! Yay!

| Schematic  | PCB | 3D Model
| ------------- | ------------- | ------------- |
|<img width="1070" height="758" alt="{B72BF1BE-3581-4B01-B1A0-090EB5490931}" src="https://github.com/user-attachments/assets/e5079a5f-18c0-4a94-b7fd-1e32930111cc" />|<img width="1070" height="758" alt="{8346E6D1-9D81-4E28-AE12-150D5CCDEE44}" src="https://github.com/user-attachments/assets/b56b6ed1-55be-4415-809e-46b2af7c200f" />|<img width="1068" height="601" alt="hackpad" src="https://github.com/user-attachments/assets/40a456d8-15ea-499c-91a7-4a12439a3c8f" />|

> [!WARNING]
> Code is untested and may need more edits!

The firmware uses the code provied and some other feautres and libaries to get this working. Controls the keys, leds, and screen. 


