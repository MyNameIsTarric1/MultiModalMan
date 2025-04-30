import speech_recognition as sr

def recognize_letter_from_phrase():
    recognizer = sr.Recognizer()

    print("🎙️  Pronuncia una lettera con la formula: 'lettera A', 'lettera B', ecc...")

    # Puoi modificare questo valore se serve un microfono specifico
    device_index = None  # Es: 5 se sai qual è il microfono giusto

    try:
        with sr.Microphone(device_index=device_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Pronto! Parla ora...")

            audio = recognizer.listen(source, timeout=5)
            print("🔎 Riconoscimento in corso...")

            text = recognizer.recognize_google(audio, language="it-IT").strip().upper()
            print(f"📝 Frase riconosciuta: {text}")

            if text.startswith("LETTERA "):
                possible_letter = text.replace("LETTERA ", "").strip()

                if len(possible_letter) == 1 and possible_letter.isalpha():
                    print(f"✅ Lettera estratta: {possible_letter}")
                    return possible_letter
                else:
                    print(f"⚠️  Hai detto 'LETTERA' ma la parte finale non è una lettera valida: {possible_letter}")
            else:
                print("❌ Frase non riconosciuta correttamente. Usa la formula: 'lettera A', 'lettera B', ...")

    except sr.WaitTimeoutError:
        print("⏱️ Tempo scaduto. Nessun suono rilevato.")
    except sr.UnknownValueError:
        print("❌ Non riesco a capire cosa hai detto.")
    except sr.RequestError as e:
        print(f"❌ Errore del servizio STT: {e}")

if __name__ == "__main__":
    recognize_letter_from_phrase()
