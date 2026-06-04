# -*- encoding=utf8 -*-
__author__ = "vera.yang"

from airtest.core.api import *
from airtest.cli.parser import cli_setup

#假设目标进程pid为10780
auto_setup(__file__, logdir=True, devices=["Windows:///?process=19496&no_embed=True"])

#初始化poco
from poco.drivers.unity3d import UnityPoco
poco = UnityPoco()

#冒烟脚本
touch(Template(r"tpl1780565988651.png", record_pos=(-0.484, -0.273), resolution=(1280, 720)))
touch(Template(r"tpl1780565996824.png", record_pos=(0.444, 0.262), resolution=(1280, 720)))
touch(Template(r"tpl1780565995440.png", record_pos=(-0.179, -0.267), resolution=(1280, 720)))
touch(Template(r"tpl1780565996824.png", record_pos=(0.444, 0.262), resolution=(1280, 720)))
touch(Template(r"tpl1780565999785.png", record_pos=(-0.116, -0.271), resolution=(1280, 720)))
touch(Template(r"tpl1780566021345.png", record_pos=(-0.009, -0.273), resolution=(1280, 720)))
touch(Template(r"tpl1780566023207.png", record_pos=(0.022, -0.227), resolution=(1280, 720)))
touch(Template(r"tpl1780566023894.png", record_pos=(0.156, -0.222), resolution=(1280, 720)))
touch(Template(r"tpl1780566025590.png", record_pos=(0.093, -0.269), resolution=(1280, 720)))
touch(Template(r"tpl1780566027159.png", record_pos=(-0.075, -0.219), resolution=(1280, 720)))
touch(Template(r"tpl1780566027624.png", record_pos=(-0.005, -0.22), resolution=(1280, 720)))
touch(Template(r"tpl1780566028115.png", record_pos=(0.071, -0.22), resolution=(1280, 720)))
touch(Template(r"tpl1780566028675.png", record_pos=(0.151, -0.224), resolution=(1280, 720)))
touch(Template(r"tpl1780566030144.png", record_pos=(0.177, -0.226), resolution=(1280, 720)))
touch(Template(r"tpl1780566030677.png", record_pos=(0.232, -0.225), resolution=(1280, 720)))
touch(Template(r"tpl1780566031496.png", record_pos=(0.173, -0.267), resolution=(1280, 720)))
touch(Template(r"tpl1780566036642.png", record_pos=(0.223, -0.216), resolution=(1280, 720)))
swipe(Template(r"tpl1780566037239.png", record_pos=(0.275, -0.223), resolution=(1280, 720)), vector=[-0.0023, 0.0042])
touch(Template(r"tpl1780566037785.png", record_pos=(0.355, -0.217), resolution=(1280, 720)))
touch(Template(r"tpl1780566038658.png", record_pos=(0.256, -0.279), resolution=(1280, 720)))
touch(Template(r"tpl1780566040077.png", record_pos=(-0.009, -0.222), resolution=(1280, 720)))
touch(Template(r"tpl1780566040679.png", record_pos=(0.066, -0.224), resolution=(1280, 720)))
touch(Template(r"tpl1780566046911.png", record_pos=(0.008, -0.266), resolution=(1280, 720)))
touch(Template(r"tpl1780566057386.png", record_pos=(0.158, -0.223), resolution=(1280, 720)))
touch(Template(r"tpl1780566059869.png", record_pos=(0.424, -0.185), resolution=(1280, 720)))
touch(Template(r"tpl1780566092595.png", record_pos=(-0.035, 0.228), resolution=(1280, 720)))
swipe(Template(r"tpl1780566097924.png", record_pos=(0.148, -0.225), resolution=(1280, 720)), vector=[1, 0.2431])

##poco实现
sleep(10)
poco(text="聊天").click()