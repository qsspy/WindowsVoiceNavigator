import speech_recognition as sr

r = sr.Recognizer()

print("Im alive")

with sr.Microphone() as source:
    print("Proszę mówić :")
    audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="pl")
        print(f"Powiedziałeś : {text}")
    except:
        print("Wybacz, nie zrozumiałem :(")
