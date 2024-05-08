import time
import framebuf
from resources.pic_power_on_pico import PowerOnPico
from resources.pic_power_on_heart import power_on_heart
from resources.pic_power_on_heartwave import power_on_heartwave
from hardware import Display

def play_power_on_animation():
    display = Display()
    for i in range(64):
        buf = framebuf.FrameBuffer(power_on_heartwave, 122, 27, framebuf.MONO_VLSB)
        display.blit(buf, 2, 0)
        display.fill_rect(63 + i, 0, 128 - 63 - i, 63, 0)
        display.fill_rect(0, 0, 63 - i, 63, 0)
        display.show()
    power_on_pico = PowerOnPico()
    for i in range(len(power_on_pico.seq)):
        buf = framebuf.FrameBuffer(power_on_pico.seq[i], 61, 29, framebuf.MONO_VLSB)
        display.blit(buf, 63, 32)
        display.show()
    time.sleep_ms(500)
    buf = framebuf.FrameBuffer(power_on_heart, 15, 13, framebuf.MONO_VLSB)
    display.blit(buf, 23, 40)
    display.show()
    time.sleep_ms(1000)
    power_on_pico.free()
    del power_on_pico
    del buf
    del display

