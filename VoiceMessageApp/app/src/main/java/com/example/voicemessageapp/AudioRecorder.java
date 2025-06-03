package com.example.voicemessageapp;

import android.content.Context;
import android.media.MediaRecorder;
import android.os.Build;
import android.util.Log;
import java.io.File;
import java.io.IOException;

public class AudioRecorder {
    private static final String TAG = "AudioRecorder";
    private MediaRecorder recorder;
    private final File outputFile;
    private boolean isRecording = false;

    public AudioRecorder(Context context) {
        outputFile = new File(context.getCacheDir(), "recording.wav");
    }

    public void startRecording() throws IOException {
        if (isRecording) {
            return;
        }

        if (recorder != null) {
            recorder.release();
        }

        recorder = new MediaRecorder();
        recorder.setAudioSource(MediaRecorder.AudioSource.MIC);
        recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
        recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
        recorder.setOutputFile(outputFile.getAbsolutePath());

        try {
            recorder.prepare();
            recorder.start();
            isRecording = true;
        } catch (IOException e) {
            Log.e(TAG, "Erreur lors du démarrage de l'enregistrement", e);
            throw e;
        }
    }

    public void stopRecording() {
        if (!isRecording) {
            return;
        }

        try {
            recorder.stop();
            recorder.release();
            isRecording = false;
        } catch (Exception e) {
            Log.e(TAG, "Erreur lors de l'arrêt de l'enregistrement", e);
        } finally {
            recorder = null;
        }
    }

    public File getOutputFile() {
        return outputFile;
    }

    public boolean isRecording() {
        return isRecording;
    }
}