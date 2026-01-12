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

| Schematic  | PCB |
| ------------- | ------------- |
|  <img width="974" height="643" alt="{43D8BD11-BAAD-4A10-A70D-C032815F9AB0}" src="https://github.com/user-attachments/assets/be0a52a8-0bc7-4c6c-bebc-8875f637c668" />| <img width="870" height="586" alt="{8FDC4C57-B847-4401-8664-15C793F48F9A}" src="https://github.com/user-attachments/assets/ac13fbcb-8ae3-49d3-9bfc-5ab2c79105cc" />

## Firmware
> [!WARNING]
> Code is untested and may need more edits!

The firmware uses the code provied and some other feautres and libaries to get this working. Controls the keys, leds, and screen. 


