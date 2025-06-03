package com.example.voicemessageapp;

public class VoiceMessage {
    private final String date;
    private final String time;
    private final String filepath;
    private boolean listened;

    public VoiceMessage(String date, String time, String filepath, boolean listened) {
        this.date = date;
        this.time = time;
        this.filepath = filepath;
        this.listened = listened;
    }

    public String getDate() { return date; }
    public String getTime() { return time; }
    public String getFilepath() { return filepath; }
    public boolean isListened() { return listened; }
    public void setListened(boolean listened) { this.listened = listened; }
}