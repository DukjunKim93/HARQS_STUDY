project = {"name": "HelloBTS", "revision": "2"}
RunnerSettings = {"webcam": "WebCam01", "athub": "COM8"}
ATHub01 = {
    "title": "ATHub",
    "type": "ATHub",
    "name": "/dev/ttyUSB1",
    "athub_dev_id": "1",
    "port": "/dev/ttyUSB1",
    "connection_type": "serial",
    "connection_info1": "/dev/ttyUSB1",
}
WebCam01 = {
    "title": "WebCam01",
    "type": "WebCam",
    "name": "C922 Pro Stream Webcam",
    "imaging_dev_id": "1",
    "connection_type": "device_index",
    "connection_info1": "1",
    "rect": "[[0,0],[1919,0],[0,1079],[1919,1079]]",
    "nickname": "\\\\?\\usb#vid_046d&pid_085c&mi_00#7&155c57c5&0&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\\global",
}
Sound01 = {
    "title": "Sound01",
    "type": "Sound",
    "name": "alsa_input.usb-audio-technica_AT2020USB_-00.analog-stereo",
    "sound_dev_id": "2",
    "connection_type": "device_index",
    "connection_info1": "alsa_input.usb-audio-technica_AT2020USB_-00.analog-stereo",
}
