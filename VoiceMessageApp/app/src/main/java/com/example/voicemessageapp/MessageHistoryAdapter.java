package com.example.voicemessageapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import java.util.List;

public class MessageHistoryAdapter extends RecyclerView.Adapter<MessageHistoryAdapter.MessageViewHolder> {
    private List<VoiceMessage> messages = new ArrayList<>();
    private final OnMessageClickListener listener;

    public interface OnMessageClickListener {
        void onMessagePlay(VoiceMessage message);
    }

    public MessageHistoryAdapter(OnMessageClickListener listener) {
        this.listener = listener;
    }

    public void updateMessages(List<VoiceMessage> newMessages) {
        this.messages = new ArrayList<>(newMessages);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public MessageViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_message, parent, false);
        return new MessageViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull MessageViewHolder holder, int position) {
        VoiceMessage message = messages.get(position);
        holder.bind(message);
    }

    @Override
    public int getItemCount() {
        return messages.size();
    }

    class MessageViewHolder extends RecyclerView.ViewHolder {
        private final TextView messageDate;
        private final TextView messageTime;
        private final TextView messageStatus;

        public MessageViewHolder(@NonNull View itemView) {
            super(itemView);
            messageDate = itemView.findViewById(R.id.messageDate);
            messageTime = itemView.findViewById(R.id.messageTime);
            messageStatus = itemView.findViewById(R.id.messageStatus);

            itemView.setOnClickListener(v -> {
                int position = getAdapterPosition();
                if (position != RecyclerView.NO_POSITION && listener != null) {
                    listener.onMessagePlay(messages.get(position));
                }
            });
        }

        public void bind(VoiceMessage message) {
            messageDate.setText(message.getDate());
            messageTime.setText(message.getTime());
            messageStatus.setText(message.isListened() ? "Écouté" : "Non écouté");
        }
    }
}