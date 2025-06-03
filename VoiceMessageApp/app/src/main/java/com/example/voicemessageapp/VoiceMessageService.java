package com.example.voicemessageapp;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.RingtoneManager;
import android.os.PowerManager;
import android.os.PowerManager.WakeLock;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.util.Log;

import androidx.core.app.NotificationCompat;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class VoiceMessageService extends Service {
    public static final String ACTION_STOP_ALARM = "com.example.voicemessageapp.STOP_ALARM";
    private static final String CHANNEL_ID = "voice_message_service";
    private static final String ALARM_CHANNEL_ID = "voice_message_alarm";
    private static final int NOTIFICATION_ID = 1;
    private static final int FOREGROUND_ID = 101;
    public static final String ACTION_NEW_MESSAGE = "com.example.voicemessageapp.NEW_MESSAGE";

    // Intervalle de vérification: 5 secondes
    private static final long CHECK_INTERVAL = 10000;


    private boolean alertInProgress = false;

    private WakeLock wakeLock;

    private long lastMessageHash = 0;
    private long lastNotificationTime = 0;
    private static final long NOTIFICATION_COOLDOWN = 60000;

    private final OkHttpClient client = new OkHttpClient();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean isRunning = false;
    private MediaPlayer alarmPlayer;
    private Vibrator vibrator;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannels();
        startForeground(FOREGROUND_ID, createForegroundNotification());
        setupVibrator();

        // Acquérir un WakeLock partiel pour empêcher le CPU de s'endormir
        PowerManager powerManager = (PowerManager) getSystemService(POWER_SERVICE);
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,
                "VoiceMessageService::WakeLockTag");
        wakeLock.acquire();
    }

    public void resetAlertState() {
        Log.i("VoiceMessageService", "Début de la réinitialisation de l'état d'alerte");

        // Réinitialiser l'état d'alerte
        alertInProgress = false;

        // Capturer le hash actuel pour éviter qu'il ne soit traité comme nouveau
        File audioFile = new File(getCacheDir(), "current_message.wav");
        if (audioFile.exists()) {
            lastMessageHash = audioFile.length() + audioFile.lastModified();
            Log.i("VoiceMessageService", "Hash du fichier mémorisé: " + lastMessageHash);
        }

        // Réinitialiser explicitement le temps de la dernière notification
        lastNotificationTime = System.currentTimeMillis();

        Log.i("VoiceMessageService", "État d'alerte complètement réinitialisé, prêt pour une nouvelle chute");
    }

    private void setupVibrator() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager vibratorManager = (VibratorManager) getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = vibratorManager.getDefaultVibrator();
        } else {
            vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        }
    }

    private void createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel serviceChannel = new NotificationChannel(
                    CHANNEL_ID,
                    "Service des messages vocaux",
                    NotificationManager.IMPORTANCE_LOW
            );

            NotificationChannel alarmChannel = new NotificationChannel(
                    ALARM_CHANNEL_ID,
                    "Alarme de nouveau message",
                    NotificationManager.IMPORTANCE_HIGH
            );
            alarmChannel.setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM),
                    new AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_ALARM)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                            .build()
            );
            alarmChannel.enableVibration(true);
            alarmChannel.setVibrationPattern(new long[]{0, 1000, 500, 1000});

            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(serviceChannel);
            manager.createNotificationChannel(alarmChannel);
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_STOP_ALARM.equals(action)) {
                stopAlarm();
                return START_STICKY;
            } else if ("com.example.voicemessageapp.RESET_ALERT".equals(action)) {
                resetAlertState();
                return START_STICKY;
            }
        }

        if (!isRunning) {
            isRunning = true;
            startPeriodicCheck();
        }

        // Assurez-vous que le service redémarre s'il est tué
        return START_STICKY;
    }

    private void startPeriodicCheck() {
        handler.post(new Runnable() {
            @Override
            public void run() {
                if (isRunning) {
                    checkForNewMessage();
                    // Reprogrammer la vérification après l'intervalle défini
                    handler.postDelayed(this, CHECK_INTERVAL);
                }
            }
        });
    }

    private void checkForNewMessage() {
        // Si une alerte est déjà en cours et non confirmée, ne pas vérifier
        if (alertInProgress) {
            Log.d("VoiceMessageService", "Une alerte est déjà en cours, attente de confirmation");
            return;
        }

        Request request = new Request.Builder()
                .url(MainActivity.SERVER_URL + "/get_audio")
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e("VoiceMessageService", "Erreur lors de la vérification: " + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful() && response.body() != null) {
                    File audioFile = new File(getCacheDir(), "current_message.wav");
                    try (FileOutputStream fos = new FileOutputStream(audioFile)) {
                        InputStream is = response.body().byteStream();
                        byte[] buffer = new byte[4096];
                        int read;
                        while ((read = is.read(buffer)) != -1) {
                            fos.write(buffer, 0, read);
                        }
                        fos.flush();

                        // Vérifier si le fichier est différent du précédent
                        if (isNewMessage(audioFile)) {
                            Log.i("VoiceMessageService", "Nouvelle chute détectée!");
                            // Marquer qu'une alerte est en cours
                            alertInProgress = true;

                            // Envoyer le broadcast et la notification
                            Intent intent = new Intent(ACTION_NEW_MESSAGE);
                            sendBroadcast(intent);
                            showAlarmNotification();
                        }
                    }
                }
            }
        });
    }

    private boolean isNewMessage(File file) {
        try {
            // Si une alerte est déjà en cours, aucun message n'est considéré comme nouveau
            if (alertInProgress) {
                Log.d("VoiceMessageService", "Une alerte est déjà en cours - ignorant le fichier");
                return false;
            }

            // Vérifier si nous sommes dans la période de cooldown
            long currentTime = System.currentTimeMillis();
            if (currentTime - lastNotificationTime < NOTIFICATION_COOLDOWN) {
                Log.d("VoiceMessageService", "En période de cooldown - ignorant les nouvelles notifications");
                return false;
            }

            // Calculer un hash simple du fichier
            long newHash = file.length() + file.lastModified();

            // Vérifier si c'est le premier démarrage ou l'initialisation
            if (lastMessageHash == 0) {
                Log.d("VoiceMessageService", "Premier démarrage, enregistrement du hash initial: " + newHash);
                lastMessageHash = newHash;
                return false;
            }

            // Vérifier si le hash a changé significativement
            if (newHash != lastMessageHash && file.length() > 100) { // Ignorer les fichiers trop petits
                Log.d("VoiceMessageService", "Nouveau message détecté: " + newHash + " (ancien: " + lastMessageHash + ")");
                lastMessageHash = newHash;
                lastNotificationTime = currentTime; // Mettre à jour le temps de la dernière notification
                return true;
            }

            // Si le hash a changé mais n'est pas significatif, mettre à jour silencieusement
            if (newHash != lastMessageHash) {
                lastMessageHash = newHash;
            }

            return false;
        } catch (Exception e) {
            Log.e("VoiceMessageService", "Erreur dans isNewMessage: " + e.getMessage());
            e.printStackTrace();
        }
        return false;
    }

    private void showAlarmNotification() {
        Intent intent = new Intent(this, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, intent, PendingIntent.FLAG_IMMUTABLE);

        Intent stopIntent = new Intent(this, VoiceMessageService.class);
        stopIntent.setAction(ACTION_STOP_ALARM);
        PendingIntent stopPendingIntent = PendingIntent.getService(
                this, 0, stopIntent, PendingIntent.FLAG_IMMUTABLE);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, ALARM_CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle("NOUVEAU MESSAGE VOCAL !")
                .setContentText("Appuyez pour écouter le message")
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setAutoCancel(true)
                .setContentIntent(pendingIntent)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setFullScreenIntent(pendingIntent, true)
                .addAction(android.R.drawable.ic_menu_close_clear_cancel,
                        "Arrêter l'alarme", stopPendingIntent);

        NotificationManager notificationManager = getSystemService(NotificationManager.class);
        notificationManager.notify(NOTIFICATION_ID, builder.build());

        playAlarm();
        startVibration();
    }

    private void stopAlarm() {
        if (alarmPlayer != null) {
            alarmPlayer.stop();
            alarmPlayer.release();
            alarmPlayer = null;
        }
        vibrator.cancel();

        NotificationManager notificationManager = getSystemService(NotificationManager.class);
        notificationManager.cancel(NOTIFICATION_ID);
    }

    private void playAlarm() {
        try {
            if (alarmPlayer != null) {
                alarmPlayer.release();
            }

            Uri alarmSound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
            alarmPlayer = new MediaPlayer();
            alarmPlayer.setDataSource(this, alarmSound);
            alarmPlayer.setAudioStreamType(AudioManager.STREAM_ALARM);
            alarmPlayer.setLooping(true);
            alarmPlayer.prepare();
            alarmPlayer.start();

            handler.postDelayed(() -> {
                if (alarmPlayer != null && alarmPlayer.isPlaying()) {
                    alarmPlayer.stop();
                    alarmPlayer.release();
                    alarmPlayer = null;
                }
            }, 30000);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void startVibration() {
        long[] pattern = {0, 1000, 500, 1000, 500, 1000};
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(pattern, 0));
        } else {
            vibrator.vibrate(pattern, 0);
        }

        handler.postDelayed(() -> vibrator.cancel(), 30000);
    }

    private Notification createForegroundNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, notificationIntent, PendingIntent.FLAG_IMMUTABLE);

        return new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Service de messages vocaux")
                .setContentText("En attente de nouveaux messages...")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pendingIntent)
                .build();
    }

    // Force une vérification immédiate (peut être appelée après une notification)
    public void forceCheck() {
        if (isRunning) {
            handler.post(this::checkForNewMessage);
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        isRunning = false;
        handler.removeCallbacksAndMessages(null);
        if (alarmPlayer != null) {
            alarmPlayer.release();
            alarmPlayer = null;
        }
        vibrator.cancel();

        // Libérer le WakeLock si nécessaire
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
        }
    }
}