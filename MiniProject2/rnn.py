import numpy as np
from keras.models import Model
from keras.layers import Input, LSTM, Dense, concatenate, Bidirectional

from normalize_frames import normalize_frames
from load_gestures import load_gestures

# 9. FORMAT DATA
gesture_sets = load_gestures()
gesture_sets = normalize_frames(gesture_sets, 36)

samples = []
labels = []

for gs in gesture_sets:
    for seq in gs.sequences:
        sample = np.vstack(list(map(lambda x: x.frame, seq.frames)))
        samples.append(sample)
        labels.append(gs.label)

X = np.array(samples)
Y = np.vstack(labels)

# Shuffle data
p = np.random.permutation(len(X))
X = X[p]
Y = Y[p]

# 10. CREATE AND TRAIN MODEL

def unidirectional_lstm(batch_size = 12, epochs = 200, latent_dim = 16):
  input_layer = Input(shape=(X.shape[1:]))
  lstm = LSTM(latent_dim)(input_layer)
  dense = Dense(latent_dim, activation='relu')(lstm)
  pred = Dense(len(gesture_sets), activation='softmax')(dense)
  model = Model(inputs=input_layer, outputs=pred)
  model.compile(loss="sparse_categorical_crossentropy", optimizer='adam', metrics=["acc"])
  M = model.fit(X,
            Y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            validation_split=0.3,
            shuffle=True)
  return M.history #receive overall acc info

def bidirectional_lstm(batch_size = 16,epochs = 200,latent_dim = 16):
  input_layer = Input(shape=(X.shape[1:]))
  lstm = Bidirectional(LSTM(latent_dim, go_backwards=True))(input_layer)
  dense = Dense(2*latent_dim, activation='relu')(lstm)
  pred = Dense(len(gesture_sets), activation='softmax')(dense)
  model = Model(inputs=input_layer, outputs=pred)
  model.compile(loss="sparse_categorical_crossentropy", optimizer='adam', metrics=["acc"])
  M = model.fit(X,
            Y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            validation_split=0.3,
            shuffle=True)
  return M.history


x = bidirectional_lstm()
print("BIDIRECTIONAL TRAINING COMPLETE")
print("-------------------------")
print ("ACC IS")
print (sum(x['val_acc'])/float(len(x['val_acc'])))





