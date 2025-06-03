package com.example.voicemessageapp;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.media.MediaPlayer;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity implements MessageHistoryAdapter.OnMessageClickListener {
    public static final String SERVER_URL = "http://10.145.197.138:5000"; // Remplacer par votre IP
    private final OkHttpClient client = new OkHttpClient();
    private MediaPlayer mediaPlayer;
    private ActivityResultLauncher<String[]> permissionLauncher;
    private AudioRecorder audioRecorder;
    private boolean isRecording = false;
    private Handler handler = new Handler(Looper.getMainLooper());

    // UI Elements
    private Button recordButton;
    private TextView recordingStatus;
    private Button playButton;
    private ProgressBar playbackProgress;
    private TextView playbackTime;
    private CardView newMessageCard;
    private RecyclerView messageHistoryRecyclerView;
    private MessageHistoryAdapter messageAdapter;
    private CardView currentPlaybackCard;

    // Playback state
    private boolean isPlaying = false;
    private int currentDuration = 0;
    private Runnable updateSeekBarRunnable;

    // Messages history
    private List<VoiceMessage> messageHistory = new ArrayList<>();

    // Broadcast receiver pour les nouveaux messages
    private BroadcastReceiver messageReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            // Montrer le nouveau message
            showNewMessage();

            // Recharger l'historique des messages pour être sûr qu'il est à jour
            loadMessageHistory();
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initializeViews();
        setupRecyclerView();
        audioRecorder = new AudioRecorder(this);
        setupPermissions();
        setupClickListeners();

        // Enregistrer le receiver avec les flags appropriés
        IntentFilter filter = new IntentFilter(VoiceMessageService.ACTION_NEW_MESSAGE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            registerReceiver(messageReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(messageReceiver, filter);
        }
        Log.d("MainActivity", "Broadcast receiver enregistré");
    }

    private void initializeViews() {
        recordButton = findViewById(R.id.recordButton);
        recordingStatus = findViewById(R.id.recordingStatus);
        playButton = findViewById(R.id.playButton);
        playbackProgress = findViewById(R.id.playbackProgress);
        playbackTime = findViewById(R.id.playbackTime);
        newMessageCard = findViewById(R.id.newMessageCard);
        messageHistoryRecyclerView = findViewById(R.id.messageHistoryRecyclerView);
        currentPlaybackCard = findViewById(R.id.currentPlaybackCard);
        Button confirmListenedButton = findViewById(R.id.confirmListenedButton);
        confirmListenedButton.setOnClickListener(v -> confirmMessageListened());

        currentPlaybackCard.setVisibility(View.GONE);
    }

    private void setupRecyclerView() {
        messageAdapter = new MessageHistoryAdapter(this);
        messageHistoryRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        messageHistoryRecyclerView.setAdapter(messageAdapter);
    }

    private void setupClickListeners() {
        recordButton.setOnClickListener(v -> toggleRecording());
        playButton.setOnClickListener(v -> togglePlayback());

        findViewById(R.id.listenNewButton).setOnClickListener(v -> {
            newMessageCard.setVisibility(View.GONE);
            playLatestMessage();
            stopAlarm();
        });



        findViewById(R.id.stopAlarmButton).setOnClickListener(v -> {
            stopAlarm();
            newMessageCard.setVisibility(View.GONE);
        });
    }

    private void stopAlarm() {
        Intent stopIntent = new Intent(this, VoiceMessageService.class);
        stopIntent.setAction(VoiceMessageService.ACTION_STOP_ALARM);
        startService(stopIntent);
    }

    private void resetAlertState() {
        Intent resetIntent = new Intent(this, VoiceMessageService.class);
        resetIntent.setAction("com.example.voicemessageapp.RESET_ALERT");
        startService(resetIntent);
    }

    private void setupPermissions() {
        permissionLauncher = registerForActivityResult(
                new ActivityResultContracts.RequestMultiplePermissions(),
                permissions -> {
                    boolean allGranted = true;
                    for (Boolean isGranted : permissions.values()) {
                        allGranted &= isGranted;
                    }
                    if (allGranted) {
                        startVoiceMessageService();
                        loadMessageHistory();
                    } else {
                        Toast.makeText(this, "Permissions nécessaires non accordées", Toast.LENGTH_LONG).show();
                    }
                }
        );

        List<String> permissionsToRequest = new ArrayList<>();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS);
            }
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.RECORD_AUDIO);
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_AUDIO)
                    != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.READ_MEDIA_AUDIO);
            }
        } else {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                    != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.WRITE_EXTERNAL_STORAGE);
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE)
                    != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.READ_EXTERNAL_STORAGE);
            }
        }

        if (!permissionsToRequest.isEmpty()) {
            permissionLauncher.launch(permissionsToRequest.toArray(new String[0]));
        } else {
            startVoiceMessageService();
            loadMessageHistory();
        }
    }

    private void confirmMessageListened() {
        // Envoyer la notification au serveur
        Request request = new Request.Builder()
                .url(SERVER_URL + "/notify_listened")
                .post(RequestBody.create("", MediaType.parse("text/plain")))
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> {
                    Toast.makeText(MainActivity.this,
                            "Erreur lors de la confirmation: " + e.getMessage(),
                            Toast.LENGTH_SHORT).show();
                });
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                runOnUiThread(() -> {
                    if (response.isSuccessful()) {
                        Toast.makeText(MainActivity.this,
                                "Écoute confirmée avec succès",
                                Toast.LENGTH_SHORT).show();
                        // Cacher la carte de lecture après confirmation
                        currentPlaybackCard.setVisibility(View.GONE);
                        // Mettre à jour l'état du message dans l'historique
                        updateMessageListenedStatus();

                        // Afficher un message pour informer l'utilisateur que le système est toujours en pause
                        Toast.makeText(MainActivity.this,
                                "Confirmation envoyée - une réinitialisation manuelle du système est nécessaire",
                                Toast.LENGTH_LONG).show();
                    } else {
                        Toast.makeText(MainActivity.this,
                                "Erreur lors de la confirmation: " + response.code(),
                                Toast.LENGTH_SHORT).show();
                    }
                });
            }
        });
    }

    private void updateMessageListenedStatus() {
        if (!messageHistory.isEmpty()) {
            VoiceMessage currentMessage = messageHistory.get(0);
            currentMessage.setListened(true);
            messageAdapter.notifyDataSetChanged();
        }
    }

    private void startVoiceMessageService() {
        Intent serviceIntent = new Intent(this, VoiceMessageService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }

        // Attendre un court instant pour que le service démarre
        handler.postDelayed(() -> {
            // Réinitialiser l'état d'alerte pour éviter des notifications au démarrage
            resetAlertState();

            // Vérifier si le serveur vient de redémarrer
            checkServerReset();
        }, 1000);
    }

    private void checkServerReset() {
        Request request = new Request.Builder()
                .url(SERVER_URL + "/reset_history")
                .post(RequestBody.create("", MediaType.parse("text/plain")))
                .build();


    }

    private void toggleRecording() {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    }

    private void startRecording() {
        try {
            audioRecorder.startRecording();
            isRecording = true;
            recordingStatus.setText("Enregistrement en cours...");
            recordButton.setBackgroundColor(getResources().getColor(android.R.color.holo_red_light));
        } catch (IOException e) {
            e.printStackTrace();
            Toast.makeText(this, "Erreur lors du démarrage de l'enregistrement",
                    Toast.LENGTH_SHORT).show();
        }
    }

    private void stopRecording() {
        audioRecorder.stopRecording();
        isRecording = false;
        recordingStatus.setText("Appuyez pour enregistrer");
        recordButton.setBackgroundColor(getResources().getColor(android.R.color.darker_gray));
        uploadRecording();
    }

    private void uploadRecording() {
        File recordingFile = audioRecorder.getOutputFile();
        if (!recordingFile.exists()) {
            Toast.makeText(this, "Fichier d'enregistrement introuvable", Toast.LENGTH_SHORT).show();
            return;
        }

        RequestBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("audio", "recording.wav",
                        RequestBody.create(MediaType.parse("audio/wav"), recordingFile))
                .build();

        Request request = new Request.Builder()
                .url(SERVER_URL + "/upload_audio")
                .post(requestBody)
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> {
                    Toast.makeText(MainActivity.this,
                            "Erreur lors de l'envoi: " + e.getMessage(),
                            Toast.LENGTH_SHORT).show();
                });
                // Ne pas supprimer le fichier en cas d'erreur
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                runOnUiThread(() -> {
                    if (response.isSuccessful()) {
                        Toast.makeText(MainActivity.this,
                                "Message envoyé avec succès",
                                Toast.LENGTH_SHORT).show();
                        // Supprimer le fichier seulement après un envoi réussi
                        recordingFile.delete();
                    } else {
                        Toast.makeText(MainActivity.this,
                                "Erreur lors de l'envoi: " + response.code(),
                                Toast.LENGTH_SHORT).show();
                    }
                });
            }
        });
    }

    private void togglePlayback() {
        if (!isPlaying) {
            playCurrentMessage();
        } else {
            pausePlayback();
        }
    }

    private void playCurrentMessage() {
        File audioFile = new File(getCacheDir(), "current_message.wav");
        if (audioFile.exists()) {
            playAudioFile(audioFile);
        } else {
            Toast.makeText(this, "Aucun message disponible", Toast.LENGTH_SHORT).show();
        }
    }

    private void playLatestMessage() {
        if (!messageHistory.isEmpty()) {
            VoiceMessage latestMessage = messageHistory.get(0);
            onMessagePlay(latestMessage);
        } else {
            Toast.makeText(this, "Aucun message disponible", Toast.LENGTH_SHORT).show();
        }
    }

    private void playAudioFile(File audioFile) {
        try {
            if (mediaPlayer != null) {
                mediaPlayer.release();
            }
            mediaPlayer = new MediaPlayer();
            mediaPlayer.setDataSource(audioFile.getPath());
            mediaPlayer.setOnPreparedListener(mp -> {
                mp.start();
                isPlaying = true;
                updatePlaybackControls();
                startPlaybackProgressUpdate();
            });
            mediaPlayer.setOnCompletionListener(mp -> {
                isPlaying = false;
                updatePlaybackControls();
                stopPlaybackProgressUpdate();
            });
            mediaPlayer.prepareAsync();
            currentPlaybackCard.setVisibility(View.VISIBLE);
            // La notification au serveur se fera maintenant via le bouton de confirmation
        } catch (IOException e) {
            e.printStackTrace();
            Toast.makeText(this, "Erreur lors de la lecture: " + e.getMessage(),
                    Toast.LENGTH_SHORT).show();
        }
    }

    private void pausePlayback() {
        if (mediaPlayer != null && mediaPlayer.isPlaying()) {
            mediaPlayer.pause();
            isPlaying = false;
            updatePlaybackControls();
            stopPlaybackProgressUpdate();
        }
    }



    private void updatePlaybackControls() {
        playButton.setText(isPlaying ? "Pause" : "Lecture");
        if (mediaPlayer != null) {
            playbackProgress.setMax(mediaPlayer.getDuration());
            updatePlaybackTime(mediaPlayer.getCurrentPosition(), mediaPlayer.getDuration());
        }
    }

    private void startPlaybackProgressUpdate() {
        updateSeekBarRunnable = new Runnable() {
            @Override
            public void run() {
                if (mediaPlayer != null && mediaPlayer.isPlaying()) {
                    int currentPosition = mediaPlayer.getCurrentPosition();
                    playbackProgress.setProgress(currentPosition);
                    updatePlaybackTime(currentPosition, mediaPlayer.getDuration());
                    handler.postDelayed(this, 100);
                }
            }
        };
        handler.post(updateSeekBarRunnable);
    }

    private void stopPlaybackProgressUpdate() {
        if (updateSeekBarRunnable != null) {
            handler.removeCallbacks(updateSeekBarRunnable);
        }
    }

    private void updatePlaybackTime(int currentPosition, int duration) {
        String currentTime = formatTime(currentPosition);
        String totalTime = formatTime(duration);
        playbackTime.setText(String.format("%s / %s", currentTime, totalTime));
    }

    private String formatTime(int milliseconds) {
        int seconds = (milliseconds / 1000) % 60;
        int minutes = (milliseconds / (1000 * 60)) % 60;
        return String.format(Locale.getDefault(), "%02d:%02d", minutes, seconds);
    }

    public void showNewMessage() {
        runOnUiThread(() -> {
            newMessageCard.setVisibility(View.VISIBLE);

            File newMessageFile = new File(getCacheDir(), "current_message.wav");
            if (newMessageFile.exists()) {
                // Sauvegarder le message avec un nom unique basé sur le timestamp
                String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault())
                        .format(new Date());
                File savedFile = new File(getCacheDir(), "message_" + timestamp + ".wav");

                try {
                    // Copier le fichier
                    copyFile(newMessageFile, savedFile);

                    // Ajouter le nouveau message à l'historique
                    Date now = new Date();
                    SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy", Locale.getDefault());
                    SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm", Locale.getDefault());

                    VoiceMessage newMessage = new VoiceMessage(
                            dateFormat.format(now),
                            timeFormat.format(now),
                            savedFile.getAbsolutePath(),
                            false
                    );

                    // Ajouter le message à l'historique et mettre à jour l'adaptateur
                    messageHistory.add(0, newMessage);
                    messageAdapter.updateMessages(messageHistory);

                    Log.d("MainActivity", "Nouveau message ajouté à l'historique: " + savedFile.getAbsolutePath());

                } catch (IOException e) {
                    e.printStackTrace();
                    Log.e("MainActivity", "Erreur lors de la sauvegarde du message: " + e.getMessage());
                }
            } else {
                Log.w("MainActivity", "Le fichier current_message.wav n'existe pas");
            }
        });
    }

    private void copyFile(File source, File dest) throws IOException {
        try (FileInputStream fis = new FileInputStream(source);
             FileOutputStream fos = new FileOutputStream(dest)) {
            byte[] buffer = new byte[4096];
            int length;
            while ((length = fis.read(buffer)) > 0) {
                fos.write(buffer, 0, length);
            }
        }
    }

    private void loadMessageHistory() {
        messageHistory.clear();

        File cacheDir = getCacheDir();
        // Rechercher tous les fichiers .wav dans le cache
        File[] files = cacheDir.listFiles((dir, name) -> name.endsWith(".wav"));
        if (files != null) {
            for (File file : files) {
                Date lastModified = new Date(file.lastModified());
                SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy", Locale.getDefault());
                SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm", Locale.getDefault());

                messageHistory.add(new VoiceMessage(
                        dateFormat.format(lastModified),
                        timeFormat.format(lastModified),
                        file.getAbsolutePath(),
                        false // Par défaut, le message n'est pas écouté
                ));
            }
        }

        // Trier l'historique par date de modification (le plus récent en premier)
        Collections.sort(messageHistory, (m1, m2) -> {
            File f1 = new File(m1.getFilepath());
            File f2 = new File(m2.getFilepath());
            return Long.compare(f2.lastModified(), f1.lastModified());
        });

        messageAdapter.updateMessages(messageHistory);
    }


    private void addMessageToHistory(String filepath) {
        Date now = new Date();
        SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy", Locale.getDefault());
        SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm", Locale.getDefault());

        VoiceMessage newMessage = new VoiceMessage(
                dateFormat.format(now),
                timeFormat.format(now),
                filepath,
                false
        );

        messageHistory.add(0, newMessage);
        messageAdapter.updateMessages(messageHistory);
    }

    @Override
    public void onMessagePlay(VoiceMessage message) {
        File audioFile = new File(message.getFilepath());
        if (audioFile.exists()) {
            playAudioFile(audioFile);
            message.setListened(true);
            messageAdapter.notifyDataSetChanged();
        }
    }

    private void notifyServerMessageListened() {
        Request request = new Request.Builder()
                .url(SERVER_URL + "/notify_listened")
                .post(RequestBody.create("", MediaType.parse("text/plain")))
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                e.printStackTrace();
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (!response.isSuccessful()) {
                    runOnUiThread(() -> Toast.makeText(MainActivity.this,
                            "Erreur serveur: " + response.code(), Toast.LENGTH_SHORT).show());
                }
            }
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (mediaPlayer != null) {
            mediaPlayer.release();
            mediaPlayer = null;
        }
        stopPlaybackProgressUpdate();
        handler.removeCallbacksAndMessages(null);
        unregisterReceiver(messageReceiver);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (isRecording) {
            stopRecording();
        }
        if (isPlaying) {
            pausePlayback();
        }
    }
}