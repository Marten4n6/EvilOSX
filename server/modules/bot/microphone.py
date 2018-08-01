import os
import sys
import time

import objc
import objc._objc
from AVFoundation import *
from Foundation import *


def run(options):
    record_time = int(options["record_time"])
    output_dir = options["output_dir"]
    output_name = options["output_name"]

    pool = NSAutoreleasePool.alloc().init()

    # Construct audio URL
    output_path = os.path.join(output_dir, output_name)
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
        "AVEncoderAudioQualityKey": 0,
        "AVEncoderBitRateKey": 16,
        "AVSampleRateKey": 44100.0,
        "AVNumberOfChannelsKey": 2,
    })

    # Create the AVAudioRecorder
    (recorder, error) = AVAudioRecorder.alloc().initWithURL_settings_error_(
        audio_url,
        audio_settings,
        objc.nil,
    )
    
    if error:
        print("Unexpected error: " + str(error))
    else:
        # Record audio for x seconds
        recorder.record()

        for i in range(0, record_time):
            try:
                time.sleep(1)
            except SystemExit:
                # Kill task called.
                print("Recording cancelled, " + str(i) + " seconds were left.")
                break

        recorder.stop()

        del pool

        # Done.
        os.rename(output_path, output_path + ".mp3")
        print("Finished recording, audio saved to: " + output_path + ".mp3")
